class InvalidHttpMethod(Exception):
    pass


class InvalidRoute(Exception):
    pass


class InvalidRequest(Exception):
    pass


class InvalidProtocol(Exception):
    pass


class TemplatesNotFound(Exception):
    pass


class WrongGetParamsPattern(Exception):
    pass


__all__ = [
    'InvalidHttpMethod',
    'InvalidRoute',
    'InvalidRequest',
    'InvalidProtocol',
    'TemplatesNotFound',
    'WrongGetParamsPattern',
]