from flask import Flask, request
from socket_server import *
from util import *
import util
import sys
import os
app = Flask(__name__)

SUCCESS_CODE = 200
ERROR_CODE = 300
ERROR_FORMAT = {
    'code': ERROR_CODE,
    'msg': "data format error"
}
ERROR_OFFLINE = {
    'code': ERROR_CODE,
    'msg': 'device offline'
}
SUCCESS_ACTION = {
    'code': SUCCESS_CODE,
    'msg': "action transfer success"
}
SUCCESS_CLIENT = {
    'code': SUCCESS_CODE,
    'msg': 'client setup success'
}


@app.route('/send_action/')
def get_order():
    action = request.args.get('action')
    id = request.args.get('id')
    if action is not None and id is not None:
        action, id = int(action), int(id)
        print("Get action %d from device %d" % (
            action, id))
        if action in util.id2mac.keys():
            mac = util.id2mac[action]
            if send(util.mac2socket[mac], {
                'action': action
            }):
                return SUCCESS_ACTION
        return ERROR_OFFLINE
    else:
        return ERROR_FORMAT


@app.route('/client_status/')
def check_client():
    client_id = request.args.get('id')
    ip = request.remote_addr
    print(ip)
    client_name = request.args.get('name')
    if client_id is not None and client_name is not None:
        print("Client device online \nDevice id : %s\nDevice name : %s" %
              (client_id, client_name))
        return SUCCESS_CLIENT
    else:
        return ERROR_FORMAT


def wait_for_exit():
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        os._exit(0)


class FlaskRun(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        print("Start Http Server...")
        app.run("0.0.0.0", 8888, debug=False)


if __name__ == '__main__':
    socket_server = SocketServer()
    socket_server.start()
    http_server = FlaskRun()
    http_server.start()
    wait_for_exit()
