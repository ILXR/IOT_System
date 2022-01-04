#!/usr/bin/python
# -*- encoding: utf-8 -*-
'''
@File     :   action_detector.py
@Time     :   2021/11/30 19:36:26
@Author   :   Yuchen Gong
@Contact  :   gyc8787@163.com
@Describe :   从 util 的 DataQueue 中检测按压动作，并向服务器发送http数据
'''

# here put the import lib
from threading import Thread
import numpy as np
from util import *
import util

# 检测按压参数
'''
maxvalue                   ---------
                           |       |                                                                              ----------
action start             ->|       |   ->   cur_value = baseline * ACTION_START_THRESHOLD                         |        |
                           |       |                                                                              |        |
action end                 |     ->|   ->   cur_value = baseline + (maxvalue - baseline) * ACTION_END_THRESHOLD   |        |
                           |       |                                                                              |        |
baseline     --------------         -------------------------- >= ACTION_INTERVAL --------------------------------          ------
'''
ACTION_START_DVAL = 10        # 和稳定值相差一定值时，按压动作开始
ACTION_END_THRESHOLD = 1/2    # 当电容相较于触发值的变化值降低为一定阈值时，按压动作结束
STABLE_THRESHOLD = 5          # 动态调整基准值（baseline）的最大极差
ACTION_INTERVAL = 5           # 每两次动作之间的最小间隔
CACHE_SIZE = 50               # 用于获取基准值的数据量
CHANNEL_IN_ACTION = None      # 当前已经进入动作的通道


class ChannelDetector():
    # 单通道数据处理器
    def __init__(self, channel_id):
        self.id = channel_id
        self.cache = []
        self.in_action = False
        self.baseline = None
        self.max_action_val = 0
        self.min_stable_val = 0
        self.action_interval = 0
        self.start_action_val = 0

    def push(self, val):
        global network_man, CHANNEL_IN_ACTION
        if len(self.cache) == CACHE_SIZE:
            # 获取通道稳定基准值
            if self.baseline is None or (np.max(self.cache) - np.min(self.cache) <= STABLE_THRESHOLD):
                self.baseline = np.mean(self.cache)
            self.cache.pop(0)
        self.cache.append(val)
        self.action_interval += 1
        if(self.baseline is None):
            return
        min_start_val = self.baseline + ACTION_START_DVAL
        if not self.in_action and (val > min_start_val) and self.action_interval > ACTION_INTERVAL \
                and val > self.min_stable_val + ACTION_START_DVAL:
            # 超出阈值，判断为Action
            self.in_action = True
            self.start_action_val = val
            if CHANNEL_IN_ACTION is None:
                # 向服务器发送动作数据（通道id）
                CHANNEL_IN_ACTION = self.id
                network_man.send_action(self.id)
        if self.in_action:
            # 记录动作最大值
            self.max_action_val = max(self.max_action_val, val)
            if(val < self.start_action_val + (self.max_action_val - self.start_action_val) * ACTION_END_THRESHOLD):
                # 下降沿，Action结束
                self.min_stable_val = val
                self.in_action = False
                self.max_action_val = 0
                self.action_interval = 0
                if CHANNEL_IN_ACTION == self.id:
                    CHANNEL_IN_ACTION = None
        else:
            self.min_stable_val = min(self.min_stable_val, val)


class DetectorThread(Thread):
    # 多通道数据处理线程
    def __init__(self):
        global CHANNELS
        self.status = util.ThreadStatus.ALIVE
        self.channels_detector = [ChannelDetector(
            i) for i in range(1, CHANNELS+1)]
        Thread.__init__(self)

    def run(self):
        global data_queue
        while (self.status == ThreadStatus.ALIVE and not util.PROGRAM_EXIT):
            try:
                data = data_queue.get(timeout=5)
                for i in range(len(data)):
                    self.channels_detector[i].push(data[i])
            except KeyboardInterrupt:
                util.PROGRAM_EXIT = True
                return
            except Exception as e:
                util.print_exception(e)
                print("Action detector exit 1")
                return


class ActionDetector():
    def __init__(self) -> None:
        self.thread = DetectorThread()

    def start_detect(self):
        self.thread.start()

    def join(self):
        self.thread.join()
