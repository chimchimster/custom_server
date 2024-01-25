import os
import importlib
import logging
import pdb
import queue
import socket
import pathlib
import sys
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils import RequestParser


class SockServer:

    def __init__(self, addr: str, port: int, event):
        self.__addr = (addr, port)
        self.__logger = self.__set_logger()
        self.__server_socket = self.__create_socket()
        self.__reload_event = event
        self.__con_events = []

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

        for con_event in self.__con_events:
            con_event.set()

        self.__server_socket.close()
        self.__reload_event.set()

        for thr_con in threading.enumerate():
            if not isinstance(thr_con, threading._MainThread) and thr_con.is_alive():
                thr_con.join()

        self.log.info('Server shut down.')

    def __accept_connection(self, soc: socket.socket):

        con, addr = soc.accept()
        addr: tuple

        if con is not None:
            self.log.info('Received connection from %s:%s address.' % addr)

            con_event = threading.Event()
            thr_con = threading.Thread(target=self.__handle_client, args=(con, con_event))
            self.__con_events.append(con_event)
            thr_con.start()


    def start_serving(self):
        self.log.info('Server started on http://%s:%s' % self.__addr)

        with self.__server_socket as soc:
            while not self.__reload_event.is_set():
                self.__accept_connection(soc)


    @staticmethod
    def __handle_client(connection, con_event):

        try:
            while True:
                data = connection.recv(1024)
                if not data or not con_event.is_set():
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

    def __init__(self, event: threading.Event):
        self.__event = event

    def on_any_event(self, event):
        if event.is_directory:
            return
        self.__event.set()


class Adapter:

    @staticmethod
    def fetch_signal(event: threading.Event):
        while not event.is_set():
            if event.is_set():
                return


def main():

    adapter_event = threading.Event()
    reload_event = threading.Event()

    observer = FSObserver()
    observer.start_observer(adapter_event)

    server = SockServer('127.0.0.1', 9999, reload_event)


    thr_server = threading.Thread(target=server.start_serving, daemon=True)
    thr_server.start()

    thr_adapt = threading.Thread(target=Adapter().fetch_signal, args=(adapter_event,))
    thr_adapt.start()
    thr_adapt.join()

    if not thr_adapt.is_alive():
        reload_event.set()
        server.shutdown()
        # thr_server.join()
        main_modname = os.path.basename(__file__)[:-3]
        module = importlib.import_module(main_modname)
        importlib.reload(module)
        globals().update(vars(module))


if __name__ == '__main__':

    try:
        while True:
            main()
    except KeyboardInterrupt:
        print('Server is not serving anymore. Goodbye :]')
        sys.exit(0)