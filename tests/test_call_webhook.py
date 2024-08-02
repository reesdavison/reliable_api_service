from uuid import uuid4

from app.enums import SignTaskStatus
from app.schemas.messages import IntSignTask

from .client_fixture import client


def test_call_webhook_success(client):
    """This test is most used to inform
    correct serialization for httpx in the call_webhook() function
    """

    t1 = IntSignTask(
        webhook_url="foo.foo.foo.1",
        message="foobar1",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    response = client.post(
        "/crypto/test-webhook", json=t1.sanitize().model_dump(mode="json")
    )
    assert response.status_code == 200
