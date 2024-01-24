import pydantic


class RequestModel(pydantic.BaseModel):
    method_name: str
    route: str
    proto: str
    headers: dict[str, str]


class RequestObj:

    def __new__(
            cls,
            method_name: str,
            route: str,
            proto: str,
            /,
            **headers,
    ):

        return RequestModel(method_name=method_name, route=route, proto=proto, headers=headers)

