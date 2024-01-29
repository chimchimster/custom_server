import logging
import socket
import threading
import select

from utils import RequestParser


logger = logging.getLogger('Server')


class SockServer:

    def __init__(self, addr: str, port: int):
        self.__addr = (addr, port)
        self.__server_socket = self.__create_socket()
        self.__shutdown_event = threading.Event()

    def __create_socket(self):
        server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server_socket.bind(self.__addr)
        server_socket.listen()
        return server_socket

    def start_serving(self):
        logger.info('Server started on http://%s:%s' % self.__addr)
        with self.__server_socket as soc:
            while not self.__shutdown_event.is_set():
                self.__accept_connection(soc)

    def __accept_connection(self, soc: socket.socket):

        rd, wr, er = select.select([soc], [], [], 1.0)
        for sk_rd in rd:
            if sk_rd is soc:
                try:
                    con, addr = sk_rd.accept()
                    addr: tuple
                    if con is not None:
                        logger.info('Received connection from %s:%s address.' % addr)
                        prc_con = threading.Thread(
                            target=self.__handle_client,
                            args=(con,),
                        )
                        prc_con.start()

                except OSError:
                    return

    @staticmethod
    def __handle_client(connection):

        while True:
            data = connection.recv(1024)
            if not data:
                connection.close()
                break
            else:
                decoded_data = data.decode('utf-8')
                pars = RequestParser(decoded_data)
                v = pars.parse_http_request()
                print(v)

    def shutdown(self):

        self.__shutdown_event.set()

        logger.info('Server has been shut down.')


if __name__ == '__main__':

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(message)s',
        datefmt='%d-%B-%Y %H:%M:%S',
    )

    s = SockServer('127.0.0.1', 9999)
    s.start_serving()
