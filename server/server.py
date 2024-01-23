import json
import socket
import threading

from utils import RequestParser


class SockServer:
    def __init__(self, addr: str, port: int):
        self.__addr = (addr, port)

    def __create_socket(self):
        server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server_socket.bind(self.__addr)
        server_socket.listen()
        return server_socket

    def start_serving(self):
        print('Server started')
        server_socket = self.__create_socket()
        while True:
            con, addr = server_socket.accept()
            print('Received connection from %s:%s address.' % addr)
            if con is not None:
                thr = threading.Thread(target=self.__handle_client, args=(con,))
                thr.start()

    @staticmethod
    def __handle_client(connection):

        while True:
            data = connection.recv(1024)
            if not data:
                break
            else:
                pars = RequestParser(data.decode('utf-8'))
                v = pars.parse_http_request()
                connection.send(json.dumps(v).encode('utf-8'))


if __name__ == '__main__':
    SockServer('127.0.0.1', 9999).start_serving()