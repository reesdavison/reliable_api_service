import asyncio

# import anyio
import base64
import logging
import socket
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from uuid import uuid4

import fastapi
import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import app.queue as queue
import app.schemas as schemas
from app.config import AppConfig
from app.constants import MAX_TASK_RETRIES, TEST_WEBHOOK_PATH
from app.enums import ServiceManagerStatus, SignTaskStatus
from app.env import get_app_config
from app.logging import get_logger, set_app_log_level
from app.service_manager import UnreliableServiceManager

logger = get_logger(__name__)


def get_unreliable_service_headers(cfg: AppConfig):
    return {"Authorization": cfg.API_KEY}


async def validate_webhook_url(url: str) -> bool:
    """We're just validating the DNS resolution here

    Avoids a bug where httpx.post() not obeying timeout
    and hanging on failed DNS lookup with async blocking the event loop
    """
    if url == f"http://localhost:8000{TEST_WEBHOOK_PATH}":
        # hack for testing
        return True

    parsed_uri = urlparse(url)
    hostname = parsed_uri.netloc
    port = None
    if parsed_uri.scheme == "https":
        port = 443
    elif parsed_uri.scheme == "http":
        port = 80
    else:
        return False

    try:
        # socket.getaddrinfo(hostname, port)
        loop = asyncio.get_running_loop()
        await loop.getaddrinfo(hostname, port)
    except socket.gaierror:
        return False
    return True


async def call_webhook(task: schemas.IntSignTask):
    # TODO this is likely to fail if user has set up a bad webhook url or due to network issues
    # Ideally you'd like give users ability to confirm health of the endpoint on setup
    # And ideally record of the event isn't deleted afterwards
    logger.debug(f"Call webhook for task={task.id} url={task.webhook_url}")
    res = None
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            res = await client.post(
                task.webhook_url, json=task.sanitize().model_dump(mode="json")
            )
    except httpx.RequestError:
        logger.exception(f"Error connecting to url={task.webhook_url}")

    if res and res.status_code != 200:
        logger.warning(
            f"Call webhook for task={task.id} url={task.webhook_url} failed!"
        )


async def queue_handler(
    ext_base_url: str,
    queue: queue.InMemoryQueue,
    manager: UnreliableServiceManager,
    on_success: Callable[[schemas.IntSignTask], Awaitable[None]],
    max_retries: int = MAX_TASK_RETRIES,
):
    try:
        while True:
            if task := queue.peak():
                status, res = await manager.call(
                    method="GET",
                    url=f"{ext_base_url}/crypto/sign?message={task.message}",
                )
                if status == ServiceManagerStatus.ACK:
                    if res.status_code == 200:
                        task.status = SignTaskStatus.SUCCESS
                        task.signature = base64.b64encode(res.content).decode("ascii")
                        # what if this webhook fails? need a backup
                        await on_success(task)
                        queue.pop()
                    else:
                        task.inc_retries()
                        if task.num_retries >= max_retries:
                            # for now let's just delete
                            # TODO setup permanent DB storage/ dead letter queue
                            queue.pop()
                            logger.debug(
                                f"Task {task.id} exceeded max retries={max_retries}, deleting... queue_len={len(queue)}"
                            )

            await asyncio.sleep(manager.time_step)
    except InterruptedError as err:
        return


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.queue = queue.InMemoryQueue()
    app.state.cfg = get_app_config()
    set_app_log_level(app.state.cfg.LOG_LEVEL)
    app.state.manager = UnreliableServiceManager(
        headers=get_unreliable_service_headers(app.state.cfg)
    )
    queue_task = asyncio.create_task(
        queue_handler(
            ext_base_url=app.state.cfg.UNRELIABLE_SERVICE_URL,
            queue=app.state.queue,
            manager=app.state.manager,
            on_success=call_webhook,
        )
    )
    yield
    queue_task.cancel()
    await app.state.manager.cleanup()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


@asynccontextmanager
async def get_async_client(request: Request):
    cfg: AppConfig = request.app.state.cfg
    headers = get_unreliable_service_headers(cfg)
    async with httpx.AsyncClient(headers=headers) as client:
        yield client


@app.get("/")
async def root(request: Request) -> Response:
    cfg: AppConfig = request.app.state.cfg
    async with get_async_client(request) as client:
        r = await client.get(cfg.UNRELIABLE_SERVICE_URL)
    return Response(status_code=r.status_code, content=r.content)


@app.post(TEST_WEBHOOK_PATH, response_model=schemas.SignTask)
async def test_webhook(request: Request, input_data: schemas.SignTask):
    logger.debug(f"Test webhook succeeded {input_data}")
    return input_data


@app.get("/crypto/sign", response_model=schemas.SignTask)
async def crypto_sign(
    request: Request,
    response: Response,
    message: str,
    webhook_url: str = "",
):
    cfg: AppConfig = request.app.state.cfg
    status, res = await request.app.state.manager.call(
        method="GET", url=f"{cfg.UNRELIABLE_SERVICE_URL}/crypto/sign?message={message}"
    )

    new_task = schemas.IntSignTask(
        webhook_url=webhook_url,
        message=message,
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    if status == ServiceManagerStatus.ACK and res.status_code == 200:
        response.status_code = 200
        new_task.status = SignTaskStatus.SUCCESS
        new_task.signature = base64.b64encode(res.content).decode("ascii")
        return new_task.sanitize()

    if not await validate_webhook_url(webhook_url):
        raise HTTPException(
            status_code=422, detail="Url did not validate or failed DNS lookup"
        )

    request.app.state.queue.add(new_task)
    response.status_code = 202
    logger.debug(f"Queue length {len(request.app.state.queue)}")
    return new_task.sanitize()

    # if r.status_code == 200:
    # return Response(status_code=res.status_code, content=res.content)
