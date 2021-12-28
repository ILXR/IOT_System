from machine import Timer
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
# Timer
ALARM_TIME = 5*1000
Alarm_Timer = Timer(0)

################################################### GPIO ##########################################################


def alarm_gpio_init():
    # 初始化GPIO
    global GPIO_PIN, GPIO_PIN_NUMBER, LED_PIN, LED_PIN_NUMBER
    print("alarm init...")
    GPIO_PIN = Pin(GPIO_PIN_NUMBER, Pin.OUT, value=1)
    LED_PIN = Pin(LED_PIN_NUMBER, Pin.OUT, value=0)


def alarm_init_default():
    global GPIO_PIN, GPIO_PIN_NUMBER, LED_PIN, LED_PIN_NUMBER
    print("set alarm status default close")
    GPIO_PIN.on()
    LED_PIN.off()


def alarm_open():
    global GPIO_PIN, LED_PIN
    print("alarm open")
    GPIO_PIN.off()
    LED_PIN.on()


def alarm_close():
    global GPIO_PIN, LED_PIN
    print("alarm close")
    GPIO_PIN.on()
    LED_PIN.off()


def alarm_ctrl():
    global Alarm_Timer
    Alarm_Timer.deinit()
    alarm_open()
    Alarm_Timer.init(period=ALARM_TIME, mode=Timer.ONE_SHOT,
                     callback=lambda t: alarm_close())


################################################### Util ##########################################################


def exit():
    sys.exit(0)


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

################################################### Net ##########################################################


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
        'name': 'ESP32',
        'type': 'Alarm'
    }
    s.send(json.dumps(device_info))
    # recv action data
    print("\nlistening to socket...")
    while True:
        try:
            length = s.recv(1)[0]
            if(length == 0):
                break
            data = s.recv(length)
            if data:
                data = bytes2json(data)
                if data is not None:
                    print("get data: ", data)
                    if 'action' in data.keys():
                        print("get action, my id: ", data['action'])
                        # TODO 实现警报控制
                        alarm_ctrl()
            else:
                time.sleep(0.01)
        except KeyboardInterrupt:
            s.close()
            exit()

################################################### Main ##########################################################


def start_serve():
    while True:
        try:
            alarm_init_default()
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
    alarm_gpio_init()
    start_serve()
