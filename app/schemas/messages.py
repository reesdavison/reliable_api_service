from uuid import UUID

from pydantic import BaseModel, Field

from app.enums import SignTaskStatus


class SignTask(BaseModel):
    id: UUID = Field(title="Task ID")
    webhook_url: str = Field(default="")
    message: str = Field(default="")
    status: SignTaskStatus = Field(title="Status of the message signing task")
    signature: str = Field(
        default="",
        title="Message signature",
        description="Provided on success, base64 encoded",
    )


class IntSignTask(SignTask):
    """Internal class"""

    num_retries: int = Field(default=0)

    def inc_retries(self):
        self.num_retries += 1

    def sanitize(self) -> SignTask:
        return SignTask.model_validate(self.model_dump())
