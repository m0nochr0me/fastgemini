from typing import Any

from pydantic import (
    AnyUrl,
    BaseModel,
    Field,
    field_validator,
    model_serializer,
    model_validator,
)

from fastgemini.enums import CRLF, GEMINI_MEDIA_TYPE, Status


class GeminiRequest(BaseModel):
    """
    Base schema for request models.
    """

    model_config = {"arbitrary_types_allowed": True}

    url: AnyUrl = Field(
        ...,
        description="The URL of the request",
    )
    cert_data: dict[str, Any] | None = Field(
        None,
        description="Client certificate data if provided",
    )
    path_params: dict[str, str] = Field(
        default_factory=dict,
        description="Path parameters extracted from the URL",
    )

    def __init__(
        self,
        url: bytes | str | AnyUrl,
        cert_data: dict[str, Any] | None = None,
    ) -> None:
        if isinstance(url, bytes):
            url = url.decode("utf-8").strip()
        super().__init__(url=url, cert_data=cert_data)

    @field_validator("url")
    @classmethod
    def validate_scheme(cls, v: AnyUrl) -> AnyUrl:
        if v.scheme != "gemini":
            raise ValueError("URL scheme must be 'gemini'")
        return v


class GeminiResponse(BaseModel):
    """
    Base schema for response models.
    """

    status: Status = Field(
        ...,
        description="The status of the response",
    )
    content_type: str | None = Field(
        default=GEMINI_MEDIA_TYPE,
        description="The content type of the response",
    )
    body: str | None = Field(
        default=None,
        description="The body of the response, if applicable",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int | Status) -> Status:
        if v < 10 or v > 69:
            raise ValueError("Status code must be between 10 and 69")
        if isinstance(v, int):
            return Status(v)
        return v

    @model_validator(mode="after")
    def check_model(self):
        if self.status == Status.SUCCESS:
            if not self.content_type:
                raise ValueError("Content-Type must be set for SUCCESS status")
            if not self.body:
                raise ValueError("Body must be set for SUCCESS status")
        return self

    @model_serializer
    def serialize(self) -> str:
        lines = [f"{self.status.value}", " "]
        if self.content_type:
            lines.append(f"{self.content_type}")
        lines.append(CRLF)
        if self.body:
            lines.append(self.body)
        return "".join(lines)
