from http_server import *
from socket_server import *


def wait_for_exit():
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        os._exit(0)


if __name__ == '__main__':
    socket_server = SocketServer()
    socket_server.start()
    http_server = FlaskRun()
    http_server.start()
    wait_for_exit()
