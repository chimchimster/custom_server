import importlib
import logging
import queue
import socket
import pathlib
import sys
import threading
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils import RequestParser


class SockServer:

    def __init__(self, addr: str, port: int):
        self.__addr = (addr, port)
        self.__logger = self.__set_logger()
        self.__server_socket = self.__create_socket()

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

    def shutdown(self, q: queue.Queue):

        self.log.info('Shutting server down...')

        q.put_nowait(True)

    def __accept_connection(self, soc: socket.socket):
        try:
            con, addr = soc.accept()
            addr: tuple
            if con is not None:
                self.log.info('Received connection from %s:%s address.' % addr)
                threading.Thread(target=self.__handle_client, args=(con,)).start()
        except BlockingIOError:
            pass

    def start_serving(self, q: queue.Queue):
        self.log.info('Server started on http://%s:%s' % self.__addr)

        with self.__server_socket as soc:
            soc.setblocking(False)
            while q.empty():
                self.__accept_connection(soc)

        self.log.info('Server stopped.')

    @staticmethod
    def __handle_client(connection):

        try:
            while True:
                data = connection.recv(1024)
                if not data:
                    break
                else:
                    decoded_data = data.decode('utf-8')
                    pars = RequestParser(decoded_data)
                    v = pars.parse_http_request()
                    print(v)
        finally:
            connection.close()


class FSObserver:

    BASE_DIR = pathlib.Path().resolve()
    OBSERVER = None

    def start_observer(self, q: queue.Queue):
        if self.OBSERVER is None or not self.OBSERVER.is_alive():
            self.OBSERVER = Observer()
            self.OBSERVER.schedule(
                ServerFileHandler(q),
                path=str(self.BASE_DIR),
                recursive=True,
            )
            self.OBSERVER.start()

    @classmethod
    def stop_observer(cls):
        if cls.OBSERVER is not None and cls.OBSERVER.is_alive():
            cls.OBSERVER.stop()
            cls.OBSERVER.join()


class ServerFileHandler(FileSystemEventHandler):

    def __init__(self, reload_queue: queue.Queue):
        self.__reload_queue = reload_queue

    def on_any_event(self, event):
        if event.is_directory:
            return
        self.__reload_queue.put(True)


class Adapter:

    @staticmethod
    def fetch_signal(q: queue.Queue):
        while q.empty():
            if not q.empty():
                break


def main():

    serving_q = queue.Queue()
    adapter_q = queue.Queue()

    observer = FSObserver()
    observer.start_observer(adapter_q)

    server = SockServer('127.0.0.1', 9999)

    thread_local_server = threading.local()
    thread_local_server.server = server

    thr_server = threading.Thread(target=thread_local_server.server.start_serving, args=(serving_q,))
    thr_server.start()

    thr_adapt = threading.Thread(target=Adapter().fetch_signal, args=(adapter_q,))
    thr_adapt.start()
    thr_adapt.join()

    if not thr_adapt.is_alive():
        thread_local_server.server.shutdown(serving_q)
        thr_server.join()
        server_module = importlib.import_module('server')
        importlib.reload(server_module)
        return


if __name__ == '__main__':

    try:
        while True:
            main_thread = threading.Thread(target=main)
            main_thread.start()
            main_thread.join()
    except KeyboardInterrupt:
        print('Program finished with status code 0. Goodbye :]')
        sys.exit(0)