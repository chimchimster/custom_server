import pydantic


class Request(pydantic.BaseModel):
    method_name: str
    route: str
    proto: str
    headers: dict[str, str]


class BadRequest(pydantic.BaseModel):
    status_code: int
    detail: str