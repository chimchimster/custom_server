import importlib
import logging
import queue
import socket
import pathlib
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils import RequestParser


class SockServer:

    def __init__(self, addr: str, port: int):
        self.__addr = (addr, port)
        self.__logger = self.__set_logger()
        self.__server_socket = self.__create_socket()
        self.__threads = []
        self.__shutdown_flag = False

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

    def shutdown(self):
        self.__shutdown_flag = True

        for thr in self.__threads:
            thr.join()

    def start_serving(self, q: queue.Queue):
        with self.__server_socket as soc:
            self.log.info('Server started on http://%s:%s' % self.__addr)

            while not self.__shutdown_flag:
                sg = q.get()
                if sg:
                    self.log.info('Shutdown signal received. Shutting down...')
                    break

                con, addr = soc.accept()
                addr: tuple
                if con is not None:
                    self.log.info('Received connection from %s:%s address.' % addr)
                    thr = threading.Thread(target=self.__handle_client, args=(con,))
                    thr.start()
                    self.__threads.append(thr)

            self.log.info('Server stopped.')

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
            sg = q.get()
            if sg:
                print(1)
                print(1)
                return sg


def main():
    adapter_q = queue.Queue()
    server_q = queue.Queue()

    server = SockServer('127.0.0.1', 9999)

    observer = FSObserver()
    observer.start_observer(adapter_q)

    thr_server = threading.Thread(target=server.start_serving, args=(server_q,), daemon=True)
    thr_server.start()

    thr_adapt = threading.Thread(target=Adapter().fetch_signal, args=(adapter_q,), daemon=True)
    thr_adapt.start()
    thr_adapt.join()

    if not thr_adapt.is_alive():
        server_q.put_nowait(True)
        server.shutdown()
        server_module = importlib.import_module('server')
        importlib.reload(server_module)
        main()


if __name__ == '__main__':
    main()