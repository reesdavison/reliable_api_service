from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class AppConfig(BaseModel):
    API_KEY: str = Field(description="Unreliable service API key")
    UNRELIABLE_SERVICE_URL: str = Field(description="Unreliable service URL")
    LOG_LEVEL: Literal["INFO", "DEBUG", "WARNING", "ERROR"]
    QUEUE_TYPE: Literal["persistent", "in_memory"] = Field(default="persistent")
    PERSISTENT_QUEUE_PATH: str = Field(
        default="", description="Path for persistent storage"
    )
    MAX_TASK_RETRIES: int = Field(
        default=5, description="Maximum number of tries before failing the task."
    )

    @model_validator(mode="after")
    def if_persistent_queue_a_path_is_required(self) -> Self:
        if self.QUEUE_TYPE == "persistent" and not self.PERSISTENT_QUEUE_PATH:
            raise ValueError("PERSISTENT_QUEUE_PATH required for QUEUE_TYPE=persistent")
        return self
