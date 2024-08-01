from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums import SignTaskStatus


class CreateSignTask(BaseModel):
    webhook_url: str = Field(default="")
    message: str = Field(default="")


class SignTask(CreateSignTask):
    id: UUID = Field(title="Task ID")
    status: SignTaskStatus = Field(title="Status of the message signing task")
    signature: str = Field(
        default="", title="Message signature", description="Provided on success"
    )
