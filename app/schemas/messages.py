from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateSignTask(BaseModel):
    webhook_url: str = Field(default="")
    message: str = Field(default="")


class SignTask(CreateSignTask):
    id: UUID = Field(title="Task ID")
