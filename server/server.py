import os
import importlib
import logging
import socket
import pathlib
import sys
import multiprocessing
import threading
import select
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils import RequestParser


class SockServer:

    def __init__(self, addr: str, port: int, event: multiprocessing.Event):
        self.__addr = (addr, port)
        self.__logger = self.__set_logger()
        self.__server_socket = self.__create_socket()
        self.__reload_event = event
        self.__con_events = []
        self.__prc_cons = []

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
        self.log.info('Shutting server down...')

        [con_event.set() for con_event in self.__con_events]

        for prc_con in self.__prc_cons:
            prc_con.terminate()

        self.__reload_event.set()

        self.log.info('Server has been shut down.')

    def __accept_connection(self, soc: socket.socket):

        rd, wr, er = select.select([soc], [], [], 1.0)
        for sk_rd in rd:
            if sk_rd is soc:
                try:
                    con, addr = sk_rd.accept()
                    addr: tuple
                    if con is not None:
                        self.log.info('Received connection from %s:%s address.' % addr)
                        con_event = multiprocessing.Event()
                        prc_con = multiprocessing.Process(
                            target=self.__handle_client,
                            args=(con, con_event),
                        )
                        self.__con_events.append(con_event)
                        self.__prc_cons.append(prc_con)
                        prc_con.start()

                except OSError:
                    return

    def start_serving(self):
        self.log.info('Server started on http://%s:%s' % self.__addr)
        with self.__server_socket as soc:
            while not self.__reload_event.is_set():
                self.__accept_connection(soc)

    @staticmethod
    def __handle_client(connection, con_event):

        while True:
            data = connection.recv(1024)
            if not data or con_event.is_set():
                connection.close()
                break
            else:
                decoded_data = data.decode('utf-8')
                pars = RequestParser(decoded_data)
                v = pars.parse_http_request()
                print(v)


class FSObserver:

    BASE_DIR = pathlib.Path().resolve()
    OBSERVER = None

    def start_observer(self, event: threading.Event):
        if self.OBSERVER is None or not self.OBSERVER.is_alive():
            self.OBSERVER = Observer()
            self.OBSERVER.schedule(
                ServerFileHandler(event),
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

    def __init__(self, __reload_event: threading.Event):
        self.__reload_event = __reload_event

    def on_any_event(self, event):
        if event.is_directory:
            return
        self.__reload_event.set()


class Adapter:

    @staticmethod
    def fetch_signal(event: threading.Event):
        while not event.is_set():
            if event.is_set():
                return


def main(__reload_event: multiprocessing.Event):

    adapter_event = threading.Event()

    observer = FSObserver()
    observer.start_observer(adapter_event)

    server = SockServer('127.0.0.1', 9999, __reload_event)

    prc_server = multiprocessing.Process(target=server.start_serving)
    prc_server.start()

    thr_adapt = threading.Thread(target=Adapter().fetch_signal, args=(adapter_event,))
    thr_adapt.start()
    thr_adapt.join()

    if not thr_adapt.is_alive():
        __reload_event.set()
        server.shutdown()
        observer.stop_observer()
        prc_server.terminate()


def reload_module():
    main_modname = os.path.basename(__file__)[:-3]
    module = importlib.import_module(main_modname)
    importlib.reload(module)
    globals().update(vars(module))


if __name__ == '__main__':

    try:
        while True:
            reload_module()
            reload_event = multiprocessing.Event()
            prc_main = multiprocessing.Process(target=main, args=(reload_event,))
            prc_main.start()
            prc_main.join()
    except KeyboardInterrupt:
        print('Server is not serving anymore. Goodbye :]')
        sys.exit(0)