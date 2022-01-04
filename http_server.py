from flask import Flask, request
from socket_server import *
from util import *
import util
import time
import sys
import os
app = Flask(__name__)

# Alarm
ALARM_INTERVAL = 2000  # 连续按压动作之间的最大间隔
ALARM_TIME = 3  # 连续按压动作次数
SWITCH_INTERVAL = 2000
SWITCH_TIME = 2

# NetWork
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
    '''
    从树莓派获取动作，并根据目标终端的不同类型进行分别处理
    请求需包含 action(发生动作的通道) / id(树莓派设备id) / time(发生动作时的时间戳) 字段
    '''
    args = request.args.to_dict()
    action, id, time = args['action'], args['id'], args['time']
    if action is not None and id is not None and time is not None:
        action, id, time = int(action), int(id), float(time)
        return process_order(action, id, time)
    else:
        return ERROR_FORMAT


def process_order(action, id, time):
    '''
    处理树莓派发送的动作数据
    目标终端类型包括 Switch(开关) / Alarm(警报器)
    '''
    print("Get action %d from device %d" % (
        action, id))
    if action in util.device_info:
        info = util.device_info[action]
        type, mac, socket = info['type'], info['mac'], info['socket']
        count, code = 1, SUCCESS_ACTION
        if(type == "Switch"):
            # 开关类型，持续 SWITCH_TIME 次动作，每两次间隔 SWITCH_INTERVAL 内时，切换状态
            # 1->2 (Open) 3->4 (Close) 5 ---(time>ALARM_INTERVAL)---> 6 (超时，重新计数)
            if(action in util.pre_action):
                pre = util.pre_action[action]
                pre_t, pre_c = pre['time'], pre['count']
                count = pre_c+1 if(round((time-pre_t)*1000)
                                   <= SWITCH_INTERVAL) else 1
                if(count >= SWITCH_TIME):
                    count = 0
                    print("switch change status")
                    code = send_action(socket, action)
        elif(type == "Alarm"):
            # 警报类型，持续 ALARM_TIME 次动作，每两次间隔 ALARM_INTERVAL 内时，开启警报
            # 1->2->...->ALARM_TIME (开启警报) ->ALARM_TIME+1->ALARM_TIME+2 (警报持续)
            # 1->2->...->n ---(time>ALARM_INTERVAL)---> 1 (超时，重新计数)
            if(action in util.pre_action):
                pre = util.pre_action[action]
                pre_t, pre_c = pre['time'], pre['count']
                count = pre_c+1 if(round((time-pre_t)*1000)
                                   <= ALARM_INTERVAL) else 1
                if(count >= ALARM_TIME):
                    print("alarm start")
                    code = send_action(socket, action)
        util.pre_action[action] = {
            'time': time,
            'count': count
        }
        print(util.pre_action[action])
        return code


def send_action(socket, action):
    '''
    向受控终端发送信号
    action 是受控终端的id，也是通道号，一一对应
    '''
    if send(socket, {
        'action': action
    }):
        return SUCCESS_ACTION
    else:
        return ERROR_OFFLINE


@app.route('/client_status/')
def check_client():
    '''
    树莓派上线时打印设备信息
    '''
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


class FlaskRun(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        print("Start Http Server...")
        app.run("0.0.0.0", 8888, debug=False)
