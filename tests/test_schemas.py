from uuid import uuid4

from app.enums import SignTaskStatus
from app.schemas.messages import IntSignTask, SignTask


def test_sanitize():

    id = uuid4()
    internal_task = IntSignTask(
        id=id,
        webhook_url="foo.com",
        message="foobar",
        status=SignTaskStatus.PENDING,
        signature="",
        num_retries=2,
    )
    public_task = internal_task.sanitize()

    assert public_task == SignTask(
        id=id,
        webhook_url="foo.com",
        message="foobar",
        status=SignTaskStatus.PENDING,
        signature="",
    )
