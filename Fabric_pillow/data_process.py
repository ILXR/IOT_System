#!/usr/bin/python
# -*- encoding: utf-8 -*-
'''
@File     :   data_process.py
@Time     :   2021/11/30 19:36:48
@Author   :   Yuchen Gong
@Contact  :   gyc8787@163.com
@Describe :   处理串口直接获取到的数据，保存到 util 的 DataQueue 中
'''

# here put the import lib
from threading import Thread
from util import *
import queue
import time
import util


def get_real_value(data):
    '''获取真实电容值'''
    res = []
    size = int(len(data)/3)
    for i in range(size):
        idnex = i*3
        val = (data[idnex])+(data[idnex+1] << 8)+(data[idnex+2] << 16)
        res.append(round(val*RELA_CAP/DIVISOR, 2))
    return res


def anlysis_data(size, order, data, crc8):
    '''分析数据'''
    if order == PCAP_DATA:
        data_size = data[0]
        return PCAP_RECV_DATA, get_real_value(data[1:data_size+1])
    elif order == PCAP_CTRL:
        status = "运行" if data[0] == 1 else "停止"
        frequency = (data[2] << 8) + data[1]
        count = (data[4] << 8) + data[3]
        print("状态：", status, "频率：", frequency, "平均次数：", count)
        return PCAP_RECV_CTRL_INFO, [status, frequency, count]
    elif order == PCAP_SINGLE:
        return PCAP_RECV_DATA, get_real_value(data)
    elif order == PCAP_ERROR:
        print("Error: ", PCAP_ERROR_DICT[data[0]])
        return PCAP_RECV_ERROR, []
    else:
        print("Error: 无法解析的命令")
        return PCAP_RECV_ERROR, []


class ProcessThread(Thread):
    def __init__(self):
        global CHANNELS
        self.status = ThreadStatus.ALIVE
        Thread.__init__(self)
        self.ChannelCache = [[] for i in range(CHANNELS)]
        self.__ChannelSum = [0 for i in range(CHANNELS)]

    def process_values(self, values):
        '''对数据做移动平均处理'''
        res = []
        if(len(self.ChannelCache[0]) == AVERAGE):
            for i in range(CHANNELS):
                self.__ChannelSum[i] += (values[i]-self.ChannelCache[i].pop(0))
                self.ChannelCache[i].append(values[i])
                res.append(round(self.__ChannelSum[i]/AVERAGE, 2))
        else:
            for i in range(CHANNELS):
                self.ChannelCache[i].append(values[i])
                self.__ChannelSum[i] += values[i]
        return res

    def run(self):
        global serial_queue, data_queue, TIMEOUT, WRITE_TO_FILE
        print("正在分析数据...")
        now = time.strftime("%Y-%m-%d %H_%M_%S", time.localtime(time.time()))
        pre, cur = None, None
        w = open('/home/pi/Program/Fabric_pillow/' +
                 now + '.data', 'w', encoding='utf-8') if WRITE_TO_FILE else None
        while(self.status == ThreadStatus.ALIVE and not util.PROGRAM_EXIT):
            try:
                pre, cur = cur, serial_queue.get(timeout=TIMEOUT)
                if([pre, cur] == PCAP_HEAD_RECV):
                    size = serial_queue.get(timeout=TIMEOUT)
                    order = serial_queue.get(timeout=TIMEOUT)
                    data = [serial_queue.get(timeout=TIMEOUT)
                            for i in range(size-2)]
                    crc8 = serial_queue.get(timeout=TIMEOUT)
                    type, result = anlysis_data(size, order, data, crc8)
                    if type == PCAP_RECV_DATA:
                        average = self.process_values(result)
                        if(len(average) > 0):
                            data_queue.put(average)
                            # print(str(average)[1:-1])
                            if WRITE_TO_FILE:
                                w.write(str(average)[1:-1]+"\n")
                                w.flush()
                    elif type == PCAP_RECV_ERROR:
                        raise Exception("串口数据接收错误")
            except queue.Empty:
                print(
                    "Serial Queue is empty, which means that uart is closed\nData processer exit 1")
                util.PROGRAM_EXIT = True
                return
            except Exception as e:
                util.print_exception(e)
                print("Data processer exit 1")
                return


class DataManager():
    def __init__(self):
        self.thread = ProcessThread()

    def start_process(self):
        '''开始处理数据'''
        self.thread.start()

    def stop_process(self):
        '''停止处理数据'''
        self.thread.status = ThreadStatus.DEAD

    def join(self):
        self.thread.join()
