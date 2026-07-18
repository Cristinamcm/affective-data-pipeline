from pydantic import BaseModel, Field


class PreprocessingRequest(BaseModel):
    configuration_name: str = Field(default="custom")
    config: dict[str, bool]