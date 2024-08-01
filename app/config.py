from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    RABBIT_MQ_HOST: str = Field(default="", description="eg ")
    API_KEY: str = Field(description="Unreliable service API key")
    UNRELIABLE_SERVICE_URL: str = Field(description="Unreliable service URL")
