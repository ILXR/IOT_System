from database import DeviceManager
import json

# 设备管理
device_info = {}  # 被控中断已上线，记录相关信息
pre_action = {}  # 某通道上一次获取到的动作信息
'''
device_info = {
    4:{'mac': '8c:ce:4e:9a:ab:e0', 'name': 'ESP32', 'type': 'Alarm', 'id': 4}
}
pre_action = {
    4:{'time':1640776885.3481781, 'count': 1}
}
'''


def json2bytes(obj):
    res = None
    try:
        res = str.encode(
            json.dumps(obj), encoding='GBK')
    except Exception as e:
        print(e, "\njson to bytes failed:", obj)
    finally:
        return res


def bytes2json(obj):
    res = None
    try:
        res = json.loads(bytes.decode(
            obj, encoding='GBK'))
    except Exception as e:
        print(e, "\nbytes to json failed:", obj)
    finally:
        return res
