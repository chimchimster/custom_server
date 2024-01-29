import logging

from oasis.servers.http import SimpleHttpServer

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(message)s',
        datefmt='%d-%B-%Y %H:%M:%S',
    )

    s = SimpleHttpServer('127.0.0.1', 9999)
    s.start_serving()
