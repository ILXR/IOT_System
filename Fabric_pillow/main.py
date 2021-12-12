import os
import sys
import serial
from serial_process import *
from data_process import *
from action_detector import *
from net_process import test_internet


def wait():
    while not util.PROGRAM_EXIT:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("检测到 ctrl-c; 程序退出...")
            os._exit(0)


def main():
    ser = serial.Serial('/dev/ttyACM0', 57600)
    if not test_internet():
        print("网络未连通，程序退出")
        return
    # 串口
    ser_manager = SerialManager(ser)
    ser_manager.start_read()
    # 数据包分析
    pro_manager = DataManager()
    pro_manager.start_process()
    # 动作检测
    act_detector = ActionDetector()
    act_detector.start_detect()
    # 和服务器通讯
    network_man.send_client_online()
    # 等待线程
    wait()


if __name__ == "__main__":
    main()
