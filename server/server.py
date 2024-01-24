import logging
import socket
import pathlib

import threading
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils import RequestParser


class SockServer:

    def __init__(self, addr: str, port: int):
        self.__addr = (addr, port)
        self.__server_socket = self.__create_socket()
        self.__logger = self.__set_logger()
        self.__observer = FSObserver(self, self.__logger)

    @property
    def log(self):
        return self.__logger

    @staticmethod
    def __set_logger():
        logger = logging.getLogger(__name__)
        logger.setLevel(level=logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt='%(asctime)s - %(message)s',
                datefmt='%d-%B-%Y %H:%M:%S'
            )
        )
        logger.addHandler(handler)
        return logger

    def __create_socket(self):
        server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server_socket.bind(self.__addr)
        server_socket.listen()
        return server_socket

    def reload_server(self):

        self.log.info('Closing server socket... Reloading...')
        self.__server_socket.close()

        try:
            self.__server_socket = self.__create_socket()
        except OSError as e:
            self.log.error(f"Failed to bind socket: {e}")
            time.sleep(1)

        self.start_serving()

    def start_serving(self):

        self.log.info('Server started on http://%s:%s' % self.__addr)

        self.__observer.start_observer()

        threads = []
        try:
            while True:
                con, addr = self.__server_socket.accept()
                addr: tuple
                self.log.info('Received connection from %s:%s address.' % addr)
                if con is not None:
                    thr = threading.Thread(target=self.__handle_client, args=(con,))
                    threads.append(thr)
                    thr.start()
        finally:
            [thr.join() for thr in threads]
            self.__observer.stop_observer()

    @staticmethod
    def __handle_client(connection):

        while True:
            data = connection.recv(1024)
            if not data:
                break
            else:
                decoded_data = data.decode('utf-8')
                pars = RequestParser(decoded_data)
                v = pars.parse_http_request()
                print(v)


class FSObserver:

    BASE_DIR = pathlib.Path().resolve()

    def __init__(self, serv, log):
        self.__observer = None
        self.__server_instance = serv
        self.__logger_instance = log

    def start_observer(self):
        self.__logger_instance.info('Hello')
        if self.__observer is None or not self.__observer.is_alive():
            self.__observer = Observer()
            self.__observer.schedule(
                ServerFileHandler(self.__server_instance, self.__logger_instance),
                path=str(self.BASE_DIR),
                recursive=True,
            )
            self.__observer.start()

    def stop_observer(self):
        if self.__observer is not None and self.__observer.is_alive():
            self.__observer.stop()
            self.__observer.join()


class ServerFileHandler(FileSystemEventHandler):

    def __init__(self, server_instance, logger_instance):
        self.__server_instance = server_instance
        self.__logger_instance = logger_instance

    def on_modified(self, event):

        if event.is_directory:
            return
        self.__logger_instance.info(f'File system has been modified.')
        self.__server_instance.reload_server()


if __name__ == '__main__':
    server_instance = SockServer('127.0.0.1', 9999)
    server_instance.start_serving()
    print()
    print()
    print()
    print()

