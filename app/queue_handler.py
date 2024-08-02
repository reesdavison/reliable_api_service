import asyncio
import base64
from collections.abc import Awaitable, Callable

from app import queue, schemas
from app.constants import MAX_TASK_RETRIES
from app.enums import ServiceManagerStatus, SignTaskStatus
from app.logging import get_logger
from app.service_manager import UnreliableServiceManager

logger = get_logger(__name__)


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
                try:
                    status, res = await manager.call(
                        method="GET",
                        url=f"{ext_base_url}/crypto/sign?message={task.message}",
                    )
                except Exception:
                    logger.exception("Call to manager failed")
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
