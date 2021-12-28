from util import *
import util
import time
import socketserver
import threading
import json
from threading import Thread
from database import *


def json2bytes(obj):
    res = None
    try:
        res = str.encode(
            json.dumps(obj), encoding='GBK')
    except Exception as e:
        print(e, "\njson to bytes failed:", obj)
    finally:
        return res


def bytes2json(obj):
    res = None
    try:
        res = json.loads(bytes.decode(
            obj, encoding='GBK'))
    except Exception as e:
        print(e, "\nbytes to json failed:", obj)
    finally:
        return res


def send(socket, json_obj):
    try:
        to_send = json2bytes(json_obj)
        socket.send(bytes([len(to_send)]))
        socket.send(to_send)
        return True
    except Exception as e:
        print(e)
        if(socket is not None):
            socket.close()
        print("设备连接断开\n")
        return False


class MyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            self.database = DeviceManager()
            while True:
                tem = self.request.recv(1024)
                if len(tem) == 0:
                    raise Exception("data length 0")
                self.data = bytes2json(tem)
                if self.data is not None:
                    print("{} recv:".format(self.client_address),
                          self.data)
                    mac, name = self.data['mac'], self.data['name']
                    info = self.database.get_device_by_mac(
                        mac) or self.database.add_device(mac, name)
                    if info is not None:
                        print("设备信息：", info)
                        util.id2mac[info[3]] = mac
                        util.mac2socket[mac] = self.request
                else:
                    print("数据格式错误")
        except Exception as e:
            print(e)
            print("连接断开：", self.client_address, "\n")
            self.request.close()

    def setup(self):
        print("连接建立：", self.client_address)


class SocketServer(Thread):
    def __init__(self):
        self.HOST = "0.0.0.0"
        self.PORT = 9999
        Thread.__init__(self)

    def run(self):
        HOST, PORT = "0.0.0.0", 9999
        self.server = socketserver.ThreadingTCPServer(
            (HOST, PORT), MyHandler)
        print("Start Socket Server...")
        self.server.serve_forever()
