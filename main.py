from machine import Pin
import ubinascii
import network
import usocket
import btree
import time
import json
import sys

# Wifi
SSID = 'AoDaMo'
PASSWD = '999999999'
# Socket
HOST = '192.168.137.1'
PORT = 9999
# ESP32 Info
MAC_ADDRESS = None
# Pin Ctrl
GPIO_PIN = None
GPIO_PIN_NUMBER = 0
LED_PIN = None
LED_PIN_NUMBER = 2
# database
DATABASE_NAME = 'mydb'
DATABASE_FILE = None
DATABASE = None
SWITCH_KEY = b'switch_key'
SWITCH_ON = b'on'
SWITCH_OFF = b'off'


def exit():
    global DATABASE, DATABASE_FILE
    if DATABASE:
        DATABASE.close()
    if DATABASE_FILE:
        DATABASE_FILE.close()
    sys.exit(0)


def get_switch_status():
    global DATABASE, SWITCH_KEY
    return DATABASE[SWITCH_KEY]


def database_init():
    global DATABASE, DATABASE_NAME
    print("database init...")
    try:
        DATABASE_FILE = open(DATABASE_NAME, 'r+b')
    except OSError:
        DATABASE_FILE = open(DATABASE_NAME, "w+b")
    DATABASE = btree.open(DATABASE_FILE)
    if(SWITCH_KEY not in DATABASE):
        DATABASE[SWITCH_KEY] = SWITCH_ON
        DATABASE.flush()
    print("database connected\n")


def switch_gpio_init():
    # 初始化GPIO
    global GPIO_PIN, GPIO_PIN_NUMBER, LED_PIN, LED_PIN_NUMBER
    print("switch init...")
    GPIO_PIN = Pin(GPIO_PIN_NUMBER, Pin.OUT, value=0)
    LED_PIN = Pin(LED_PIN_NUMBER, Pin.OUT, value=1)
    print("switch default on\n")


def switch_init_default():
    global GPIO_PIN, GPIO_PIN_NUMBER, LED_PIN, LED_PIN_NUMBER
    print("set switch status default on")
    GPIO_PIN.off()
    LED_PIN.on()


def switch_init_memory():
    global DATABASE, GPIO_PIN, LED_PIN
    print("set switch status according to the last setting")
    if get_switch_status() == SWITCH_ON:
        switch_open()
    else:
        switch_close()


def switch_open():
    global DATABASE, GPIO_PIN, LED_PIN
    GPIO_PIN.off()
    LED_PIN.on()
    DATABASE[SWITCH_KEY] = SWITCH_ON
    print("switch open")
    DATABASE.flush()


def switch_close():
    global DATABASE, GPIO_PIN, LED_PIN
    GPIO_PIN.on()
    LED_PIN.off()
    DATABASE[SWITCH_KEY] = SWITCH_OFF
    print("switch close")
    DATABASE.flush()


def switch_ctrl():
    # 切换继电器状态
    global DATABASE, GPIO_PIN, LED_PIN
    if get_switch_status() == SWITCH_ON:
        # open to close
        switch_close()
    else:
        # close to open
        switch_open()


def json2bytes(obj):
    res = None
    try:
        res = str.encode(
            json.dumps(obj), 'GBK')
    except Exception as e:
        print(e, "\njson to bytes failed:", obj)
    finally:
        return res


def bytes2json(obj):
    res = None
    try:
        res = json.loads(bytes.decode(
            obj, 'GBK'))
    except Exception as e:
        print(e, "\nbytes to json failed:", obj)
    finally:
        return res


def wifi_connect():
    global MAC_ADDRESS
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(SSID, PASSWD)
        while not wlan.isconnected():
            try:
                time.sleep(0.1)
            except KeyboardInterrupt:
                exit()
    print('wifi connected to ', SSID)
    print('network config: [local ip: {}\tgateway: {}\tdns: {}]'.format(
        wlan.ifconfig()[0], wlan.ifconfig()[2], wlan.ifconfig()[3]))
    MAC_ADDRESS = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    print("mac address: ", MAC_ADDRESS, "\n")


def socket_connect():
    global MAC_ADDRESS
    s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    info = usocket.getaddrinfo(HOST, PORT, 0, usocket.SOCK_STREAM)
    print("socket info: ", info, info[0][-1])
    print("socket connecting...")
    s.connect(info[0][-1])
    print("socket connected\n")
    # send device info
    device_info = {
        'mac': MAC_ADDRESS,
        'name': 'ESP32'
    }
    s.send(json.dumps(device_info))
    # 一切初始化成功，这时再根据数据库来修改开关状态
    switch_init_memory()
    # recv action data
    print("\nlistening to socket...")
    while True:
        try:
            data = s.recv(1024)
            if data:
                data = bytes2json(data)
                if data is not None:
                    print("get data: ", data)
                    if 'action' in data.keys():
                        print("get action, my id: ", data['action'])
                        switch_ctrl()
            else:
                time.sleep(0.01)
        except KeyboardInterrupt:
            s.close()
            exit()


def start_serve():
    while True:
        try:
            switch_init_default()
            wifi_connect()
            time.sleep(0.5)
            socket_connect()
        except KeyboardInterrupt as e:
            exit()
        except Exception as e:
            print(e)
            time.sleep(1)
            print("---------- retry main -----------")
            continue


def main():
    print("---------- start main -----------")
    database_init()
    switch_gpio_init()
    start_serve()
