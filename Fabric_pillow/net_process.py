from concurrent.futures import ThreadPoolExecutor
from time import sleep
from util import *
import subprocess
import requests
import time
import util
import re

# Http parm
HOST_URL = '192.168.137.1'
HOST_PORT = '8888'
SEND_ACTION_INTERFACE = 'http://'+HOST_URL+':'+HOST_PORT+'/send_action'
CLIENT_ONLINE_INTERFACE = 'http://'+HOST_URL+':'+HOST_PORT+'/client_status'

DEVICE_ID = 0
DEVICE_NAME = "树莓派"

SUCCESS_CODE = 200
ERROR_CODE = 300

HTTP_SUCCESS = 1
HTTP_FAILED = -1


def test_internet():
    # 测试服务器是否连通
    cnt = 100
    print("开始测试网络(间隔2s)...")
    for i in range(cnt):
        print('测试网络 第{}次...'.format(i+1))
        ftp_res = subprocess.Popen(
            'ping '+HOST_URL+' -c 2 -w 3', stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        res = ftp_res.stdout.read()
        str_res = res.decode("gbk")
        # 查找返回结果
        res_s = re.search("ttl", str_res)
        if res_s:
            print('网络已连通')
            return True
        else:
            sleep(2)
    return False


def http_client_online(url=CLIENT_ONLINE_INTERFACE, id=DEVICE_ID, name=DEVICE_NAME):
    # 发送设备信息，表示已上线
    param = {'id': DEVICE_ID, 'name': DEVICE_NAME}
    try:
        response = requests.get(url=url, params=param, timeout=(5, 5))
        response.raise_for_status()
        code = response.json()['code']
        if(code != SUCCESS_CODE):
            raise Exception("Return error code："+code)
        print("Send device info succeed")
        return HTTP_SUCCESS
    except Exception as e:
        print("Send device info failed")
        util.print_exception(e)
        return HTTP_FAILED


def http_send_action(url=SEND_ACTION_INTERFACE, action=None):
    # 发送动作信号
    if action is None:
        print("Http Error: Action can't be None")
        return
    param = {'id': DEVICE_ID, 'action': action, 'time': time.time()}
    try:
        response = requests.get(url=url, params=param, timeout=(5, 5))
        response.raise_for_status()
        code = response.json()['code']
        if(code != SUCCESS_CODE):
            raise Exception("return code error : "+response.json()['msg'])
        print("Send action %d succeed" % action)
        return HTTP_SUCCESS
    except Exception as e:
        print("Send action %d failed" % action)
        print(e)
        return HTTP_FAILED


def get_result(future):
    # 异步处理http返回
    if future.result() == HTTP_FAILED:
        # util.PROGRAM_EXIT = True
        pass


class NetworkManager():
    def __init__(self) -> None:
        '''用于向Server发送动作数据'''
        self.pool = ThreadPoolExecutor(max_workers=10)

    def send_action(self, action):
        futurel = self.pool.submit(
            http_send_action, SEND_ACTION_INTERFACE, action)
        futurel.add_done_callback(get_result)

    def send_client_online(self):
        futurel = self.pool.submit(
            http_client_online)
        futurel.add_done_callback(get_result)

    def __del__(self):
        self.pool.shutdown()
