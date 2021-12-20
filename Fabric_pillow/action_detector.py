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
from util import *
from threading import Thread
import numpy as np
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
ACTION_START_THRESHOLD = 1.4  # 检测到按压时电容相较于稳定状态的倍率
ACTION_END_THRESHOLD = 1/3  # 按压动作结束时，电容变化值相较于本次动作电容最大变化值的比率（下降沿时触发动作）
STABLE_THRESHOLD = 5       # 动态调整基准值的最大极差
ACTION_INTERVAL = 20       # 每两次动作之间的最小间隔
CACHE_SIZE = 50            # 用于获取基准值的数据量
CHANNEL_IN_ACTION = None   # 当前是否已经有其他通道进入动作


class ChannelDetector():
    # 单通道数据处理器
    def __init__(self, channel_id):
        self.id = channel_id
        self.cache = []
        self.in_action = False
        self.baseline = None
        self.max_action_val = 0
        self.action_interval = 0

    def push(self, val):
        global network_man, CHANNEL_IN_ACTION
        if len(self.cache) == CACHE_SIZE:
            # 获取通道稳定基准值
            if self.baseline is None or (np.max(self.cache) - np.min(self.cache) <= STABLE_THRESHOLD):
                self.baseline = np.mean(self.cache)
            self.cache.pop(0)
        self.cache.append(val)
        self.action_interval += 1
        if not self.in_action and (self.baseline is not None) and (val > self.baseline*ACTION_START_THRESHOLD) \
                and self.action_interval > ACTION_INTERVAL:
            # 超出阈值，判断为Action
            self.in_action = True
            if CHANNEL_IN_ACTION is None:
                CHANNEL_IN_ACTION = self.id
        if self.in_action:
            # 记录动作最大值
            self.max_action_val = max(self.max_action_val, val)
            if(val <  self.baseline + (self.max_action_val - self.baseline) * ACTION_END_THRESHOLD):
                # 检测下降沿，降低为峰值的一定比率时，Action结束
                self.in_action = False
                self.max_action_val = 0
                self.action_interval = 0
                if CHANNEL_IN_ACTION == self.id:
                    # 向服务器发送动作数据（通道id）
                    network_man.send_action(self.id)
                    CHANNEL_IN_ACTION = None


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
