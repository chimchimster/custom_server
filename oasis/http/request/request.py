import re

from dataclasses import dataclass

from oasis.exceptions.exc import WrongGetParamsPattern
from urllib.parse import parse_qs


class Request:

    def __init__(
            self,
            *,
            method_name: str,
            proto: str,
            route: str,
            headers: dict[str, str]
    ):
        self._method_name = method_name
        self._proto = proto
        self._route = route
        self._headers = headers

    @property
    def route(self):
        return self._route

    @property
    def method(self):
        return self._method_name

    def validate(self):

        if self._method_name == 'GET':
            self.__rebuild_route()

    def __rebuild_route(self):

        if params := re.search(r'\?.*$', self._route):
            prm = params.group()
            self.__check_if_params_valid(prm)
            setattr(self, 'GET', self.__build_params(prm))
            self._route = re.split(r'\?', self._route, maxsplit=1)[0]

    @staticmethod
    def __check_if_params_valid(params: str):

        if not re.match(r'\?(\w+=[\w\d]+&?)+', params):
            raise WrongGetParamsPattern('Invalid parameters in GET request.')

    @staticmethod
    def __build_params(params: str):

        params_to_parse = parse_qs(params[1:])

        return {key: value for key, value in params_to_parse.items()}


@dataclass
class BadRequest:
    status_code: int
    detail: str