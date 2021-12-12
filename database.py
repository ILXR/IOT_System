import sqlite3
import traceback

DATABASE = 'devices.db'

SQL_INSERT = 'INSERT INTO Device_Info (MAC,NAME,DESCRIBE,ID)\
    VALUES (?,?,?,?)'
SQL_SEARCH_ID = 'SELECT * FROM Device_Info WHERE ID = ?'
SQL_SEARCH_MAC = 'SELECT * FROM Device_Info WHERE MAC = ?'
SQL_MAX_ID = 'SELECT MAX(ID) FROM Device_Info'


class DeviceManager():
    def __init__(self):
        self.connect_database()

    def connect_database(self):
        global DATABASE
        self.conn = sqlite3.connect(DATABASE)
        self.cursor = self.conn.cursor()
        print("Database connect succeed")

    def get_max_id(self):
        self.cursor.execute(SQL_MAX_ID)
        max_id = self.cursor.fetchone()[0]
        return max_id

    def add_device(self, mac, name, describe=''):
        try:
            max_id = self.get_max_id()
            max_id = 0 if max_id is None else max_id
            self.cursor.execute(
                SQL_INSERT, (mac, name, describe, max_id+1))
            self.conn.commit()
            print("Add device succeed:\tmac: {}\tname: {}\tid: {}".format(
                mac, name, max_id+1))
            return (mac, name, describe, max_id+1)
        except Exception as e:
            print("Add device error")
            print(e)
            return None

    def get_device_by_id(self, id):
        self.cursor.execute(SQL_SEARCH_ID, (id,))
        data = self.cursor.fetchone()
        return data

    def get_device_by_mac(self, mac):
        self.cursor.execute(SQL_SEARCH_MAC, (mac,))
        data = self.cursor.fetchone()
        return data
