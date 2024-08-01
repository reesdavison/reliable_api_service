import asyncio
import time
from contextlib import asynccontextmanager
from typing import Generator
from uuid import uuid4

import fastapi
import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response

import app.queue as queue
import app.schemas as schemas
from app.config import AppConfig
from app.enums import ServiceManagerStatus, SignTaskStatus
from app.env import get_app_config
from app.service_manager import UnreliableServiceManager


def get_unreliable_service_headers(cfg: AppConfig):
    return {"Authorization": cfg.API_KEY}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.queue = queue.InMemoryQueue()
    app.state.cfg = get_app_config()
    app.state.manager = UnreliableServiceManager(
        headers=get_unreliable_service_headers(app.state.cfg)
    )
    yield
    await app.state.manager.cleanup()


app = FastAPI(lifespan=lifespan)


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


# class ClientHelper:
#     def __init__(self):
#         self.client = httpx.AsyncClient()

#     async def make_a_call(self, method, *args, **kwargs):
#         try:
#             res = await self.client.request(method=method, *args, **kwargs)
#         except httpx.CloseError as e:
#             # this empirically seems to be the right exception to catch for a remote reset,
#             # but the docstring actually states this indicates failure *to close* a connection,
#             # not failure making or using an existing connection
#             await self._reset_client()
#             res = await self.client.request(method=method, *args, **kwargs)
#         except httpx.HTTPError:
#             await self._reset_client()
#             raise Exception("Failed to connect to API, try again later.")
#         return res

#     async def _reset_client(self):
#         try:
#             await self.client.aclose()
#         finally:


@app.get("/crypto/sign", response_model=schemas.SignTask)
async def crypto_sign(
    request: Request,
    response: Response,
    message: str,
    webhook_url: str = "",
):
    cfg: AppConfig = request.app.state.cfg

    print("MESSAGE", message, "webhook_url", webhook_url)
    # print(f"{cfg.UNRELIABLE_SERVICE_URL}/crypto/sign/?message={message}")
    # return schemas.SignTask(message=message, id=uuid4(), webhook_url=webhook_url)

    status, res = await request.app.state.manager.call(
        method="GET", url=f"{cfg.UNRELIABLE_SERVICE_URL}/crypto/sign?message={message}"
    )
    new_task = schemas.SignTask(
        webhook_url=webhook_url,
        message=message,
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    if status == ServiceManagerStatus.ACK and res.status_code == 200:
        response.status_code = 200
        new_task.status = SignTaskStatus.SUCCESS
        new_task.signature = res.content
        return new_task

    request.app.state.queue.add(new_task)
    response.status_code = 202

    print("QUEUE ", request.app.state.queue.queue)
    return new_task

    # if r.status_code == 200:
    # return Response(status_code=res.status_code, content=res.content)
