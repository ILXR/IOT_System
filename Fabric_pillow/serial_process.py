from threading import Thread
from util import *
import time
import util


class ReadThread(Thread):
    def __init__(self, ser):
        self.comm = ser
        self.status = ThreadStatus.ALIVE
        Thread.__init__(self)

    def run(self):
        global serial_queue, TIMEOUT
        print("串口已开启...")
        while(self.status == ThreadStatus.ALIVE and not util.PROGRAM_EXIT):
            try:
                cnt = self.comm.in_waiting
                if(cnt > 0):
                    recv = self.comm.read(cnt)
                    for byte_data in recv:
                        serial_queue.put(byte_data, timeout=TIMEOUT)
                else:
                    time.sleep(0.1)
            except Exception as e:
                util.print_exception(e)
                util.PROGRAM_EXIT = True
                print("Serial process exit 1")
                return


class SerialManager():
    def __init__(self, ser):
        self.comm = ser
        self.thread = ReadThread(ser)

    def start_read(self):
        '''开始从串口读取数据'''
        self.thread.start()

    def stop_read(self):
        '''停止从串口读取数据'''
        self.thread.status = ThreadStatus.DEAD

    def start_measurement(self):
        '''向PCAP02发送命令，开始定时测量'''
        if(self.comm.writable()):
            self.comm.write(PCAP_CTRL_START_ORDER)

    def stop_measurement(self):
        '''向PCAP02发送命令，停止定时测量'''
        if(self.comm.writable()):
            self.comm.write(PCAP_CTRL_STOP_ORDER)

    def join(self):
        self.thread.join()
