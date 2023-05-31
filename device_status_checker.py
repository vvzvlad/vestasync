import paho.mqtt.client as mqtt
import time
import os
from collections import Counter
import argparse

parser = argparse.ArgumentParser(description="MQTT Device Error Status")
parser.add_argument("-a", "--wb", type=str, required=True, help="WB address")
args = parser.parse_args()

def get_modbus_devices():
    devices = {}
    def on_connect(client, userdata, flags, rc):
        client.subscribe("/devices/+/meta/driver")

    def on_message(client, userdata, msg):
        if msg.payload.decode() == "wb-modbus":
            device_name = msg.topic.split('/')[2]
            devices[device_name] = {}

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.wb, 1883, 60)
    client.loop_start()
    time.sleep(3)
    client.loop_stop()
    client.unsubscribe("/devices/+/meta/driver")
    client.disconnect()
    return devices

def get_all_controls(devices):
    def on_connect(client, userdata, flags, rc):
        for device in devices.keys():
            client.subscribe(f"/devices/{device}/controls/+")

    def on_message(client, userdata, msg):
        device = msg.topic.split('/')[2]
        control = msg.topic.split('/')[-1]
        devices[device][control] = "noerror"

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.wb, 1883, 60)
    client.loop_start()
    time.sleep(3)
    client.loop_stop()
    client.disconnect()
    return devices

def get_all_controls_errors(devices):
    def on_connect(client, userdata, flags, rc):
        for device, controls in devices.items():
            for control in controls.keys():
                client.subscribe(f"/devices/{device}/controls/{control}/meta/error")

    def on_message(client, userdata, msg):
        error = msg.payload.decode()
        device = msg.topic.split('/')[2]
        control = msg.topic.split('/')[4]
        if any(char in error for char in ['r', 'w']):
            devices[device][control] = "readwriteerror"
        elif error == "p":
            devices[device][control] = "perioderror"
        else:
            devices[device][control] = "noerror"

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.wb, 1883, 60)
    client.loop_start()

def sort_devices(devices):
    sorted_devices = sorted(devices.items(), key=lambda item: item[0])
    sorted_devices = sorted(sorted_devices, key=lambda item: sum(value == "readwriteerror" for value in item[1].values()), reverse=True)
    return sorted_devices


print("Get devices...")
devices = get_modbus_devices()
print("Get controls...")
devices = get_all_controls(devices)
print("Subscribe errors...")
get_all_controls_errors(devices)

lines_printed = 0
while True:
    time.sleep(1)
    # Move the cursor up and clear the line for each line printed in the last iteration
    for _ in range(lines_printed):
        print("\033[F\033[K", end="")
    lines_printed = 0

    print("Device error status:")
    lines_printed += 1
    sorted_devices = sort_devices(devices)
    max_device_name_length = max(len(device) for device, _ in sorted_devices)
    print(f"+{'-'*(max_device_name_length+2)}+{'-'*7}+{'-'*7}+{'-'*8}+{'-'*8}+")
    print(f"| {'Device':<{max_device_name_length}} | {'All':<5} | {'R/W':<5} | {'Period':<5} | {'Normal':<5} |")
    print(f"+{'-'*(max_device_name_length+2)}+{'-'*7}+{'-'*7}+{'-'*8}+{'-'*8}+")
    lines_printed += 3
    for device, controls in sorted_devices:
        error_counter = Counter(controls.values())
        normal = len(controls) - error_counter['readwriteerror']
        if normal != len(controls):
            if normal == 0:
                print("\033[31m", end="")  # Start red color
            print(f"| {device:<{max_device_name_length}} | {len(controls):<5} | {error_counter['readwriteerror']:<5} | {error_counter['perioderror']:<6} | {normal:<6} |")
            lines_printed += 1
            if normal == 0:
                print("\033[0m", end="")  # Reset color

    print(f"+{'-'*(max_device_name_length+2)}+{'-'*7}+{'-'*7}+{'-'*8}+{'-'*8}+")
    lines_printed += 1

