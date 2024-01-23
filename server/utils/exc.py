class InvalidHttpMethod(Exception):
    pass


class InvalidRoute(Exception):
    pass


class InvalidRequest(Exception):
    pass


class InvalidProtocol(Exception):
    pass


__all__ = [
    'InvalidHttpMethod',
    'InvalidRoute',
    'InvalidRequest',
    'InvalidProtocol',
]