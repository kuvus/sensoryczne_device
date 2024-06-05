import sys
import os
import time
import json
import atexit
import requests
import aes

import RPi.GPIO as GPIO

from smbus2 import SMBus
from mlx90614 import MLX90614

# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from DFRobot_BloodOxygen_S import *

# Load config.json
CONFIG = None
with open('config.json') as f:
    CONFIG = json.load(f)


API_URL = CONFIG['api_url']

TOKEN = None
KEY = None
IV = None


# API functions

def authenticate():
    global TOKEN
    global KEY
    global IV

    print("Authenticating...")

    if not CONFIG['login'] or not CONFIG['password']:
        print("login or password not set in config.json")
        return False
    
    if not CONFIG['configured']:
        print("Registering device...")
        data = {
            "login": CONFIG['login'],
            "password": CONFIG['password'],
            "name": CONFIG['name']
        }

        response = requests.post(API_URL + "/Device/register", json=data)

        if response.status_code == 200:
            print("Device registered")
            CONFIG['configured'] = True
            with open('config.json', 'w') as f:
                json.dump(CONFIG, f, indent=4)

            json_data = response.json()

            TOKEN = json_data['token']
            KEY = json_data['key']
            IV = json_data['iv']

            return True
        else:
            print("Device registration failed")
            return False

    data = {
        "login": CONFIG['login'],
        "password": CONFIG['password']
    }

    response = requests.post(API_URL + "/Device/connect", json=data)

    if response.status_code == 200:
        print("Authenticated")

        json_data = response.json()

        TOKEN = json_data['token']
        KEY = json_data['key']
        IV = json_data['iv']

        return True
    
    print("Authentication failed")
    return False


def send_data(temperature: float, ambientTemperature: int, heart_rate: int, spo2: int):
    print({
        "temperature": temperature,
        "pulseRate": heart_rate,
        "spo2": spo2,
    })

    data = {
        "temperature": aes.encrypt(str(temperature), KEY, IV),
        "pulseRate": aes.encrypt(str(heart_rate), KEY, IV),
        "spo2": aes.encrypt(str(spo2), KEY, IV),
    }

    response = requests.post(API_URL + "/Device/data", json=data, headers={ 
        "Authorization": "Bearer " + TOKEN})
    
    print(response.status_code)


'''
  ctype=1：UART
  ctype=0：IIC
'''

I2C_1       = 0x01               # I2C_1 Use i2c1 interface (or i2c0 with configuring Raspberry Pi file) to drive sensor
I2C_ADDRESS = 0x57               # I2C device address, which can be changed by changing A1 and A0, the default address is 0x77
max30102 = DFRobot_BloodOxygen_S_i2c(I2C_1 ,I2C_ADDRESS)

BUS = SMBus(1)
SENSOR = MLX90614(BUS, address=0x5A)

def end_program():
    print("Stopping program...")
    max30102.sensor_end_collect()
    BUS.close()
    return True
 
def setup():
    print("init max30102...")
    while (False == max30102.begin()):
        print("init fail!")
        time.sleep(1)
    print("start measuring...")
    max30102.sensor_start_collect()
    time.sleep(1)
  
def loop():
    max30102.get_heartbeat_SPO2()
    # print("SPO2 is : "+str(max30102.SPO2)+"%") 
    # print("heart rate is : "+str(max30102.heartbeat)+"Times/min")
    # print (SENSOR.get_amb_temp())
    # print (SENSOR.get_obj_temp())
    send_data(SENSOR.get_obj_temp(), SENSOR.get_amb_temp(), max30102.heartbeat, max30102.SPO2)
    time.sleep(1)

if __name__ == "__main__":
    atexit.register(end_program)
    if not authenticate():
        sys.exit(1)
    setup() 
    while True:
        loop()

    