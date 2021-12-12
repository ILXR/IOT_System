from net_process import NetworkManager
from enum import Enum
import queue
import traceback

# global variabal
# producer-consumer queue
serial_queue = queue.Queue(maxsize=2*1024)  # 串口数据缓存
data_queue = queue.Queue(maxsize=1024/2)  # 解析数据缓存
# httpclient
network_man = NetworkManager()

# Global flag
WRITE_TO_FILE = False
PROGRAM_EXIT = False

# Alogrithm param
TIMEOUT = 5
CHANNELS = 5
CACHE_SIZE = 100
AVERAGE = 15


class ThreadStatus(Enum):  # 控制线程运行
    ALIVE = 1
    DEAD = 0


# 格式：前导字+长度+命令+数据+校验（CRC8，格式 8541）
# 前导字，2Byte，固定的字符，收发不同；
# 长度：1Byte，是命令+数据+校验的所有字节数
# 命令：1Byte
# 校验：1Byte，是对命令+数据部分进行 CRC8 校验。
# Order
PCAP_ERROR = 0x50
PCAP_SINGLE = 0x54
PCAP_CTRL = 0x55
PCAP_DATA = 0x56
PCAP_START = 0x01
PCAP_STOP = 0x00

# Head
PCAP_HEAD_SEND = [0x68, 0xA9]
PCAP_HEAD_RECV = [0x63, 0xF3]

# Single measurement order
PCAP_SINGLE_ORDER = PCAP_HEAD_SEND.extend([0x03, PCAP_SINGLE, 0x55, 0xA8])
# Timing measurement control order
PCAP_CTRL_START_ORDER = PCAP_HEAD_SEND.extend(
    [0x03, PCAP_CTRL, PCAP_START, 0x8A])
PCAP_CTRL_STOP_ORDER = PCAP_HEAD_SEND.extend(
    [0x03, PCAP_CTRL, PCAP_STOP, 0x4E])

# Exception Info
PCAP_ERROR_DICT = {
    0x01: "接收到的数据校验不正确",
    0x02: "接收到的数据包长度不正",
    0x03: "功能不存在",
    0x04: "返回的长度不正确",
    0x05: "采样频率过快"
}

# Recv data type
PCAP_RECV_ERROR = -1
PCAP_RECV_CTRL_INFO = 0
PCAP_RECV_DATA = 1

# Process value
DIVISOR = 1 << 20
RELA_CAP = 5


def print_exception(e):
    '''打印异常信息'''
    print(str(Exception))
    print(str(e))
    print(traceback.format_exc())
