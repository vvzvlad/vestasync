#!/usr/bin/env python3
import subprocess
import re
import os
import json

def restart_service():
    subprocess.Popen(["systemctl", "restart", "wb-mqtt-serial"], stdout=subprocess.PIPE)

def parse_config_file(filename):
    with open(filename, "r") as file:
        config_data = json.load(file)

    device_to_port = {}
    device_errors = {}
    for port in config_data["ports"]:
        for device in port["devices"]:
            device_to_port[device["slave_id"]] = port["path"]
            device_errors[device["slave_id"]] = 0  # Initialize error count as zero

    return device_to_port, device_errors

def parse_journal(device_to_port, device_errors):
    p = subprocess.Popen(["journalctl", "-f", "-u", "wb-mqtt-serial"], stdout=subprocess.PIPE)
    last_log_line = None

    for line in iter(p.stdout.readline, b''):
        line = line.decode('utf-8')  # convert bytes to string
        match = re.search(r'modbus:(\d+): Serial protocol error: request timed out', line)
        if match:
            device_number = match.group(1)
            device_errors[device_number] += 1
        last_log_line = line

        # clear the console
        os.system('cls' if os.name == 'nt' else 'clear')

        # print the last log line
        print(f"Last log line: {last_log_line}")

        # print error statistics
        print_error_statistics(device_errors, device_to_port)

def print_error_statistics(device_errors, device_to_port):
    print("\n--- Error Statistics ---")

    # sort by error count
    sorted_device_errors = sorted(device_errors.items(), key=lambda x: x[1], reverse=True)

    for device, error_count in sorted_device_errors:
        device_port = device_to_port.get(device, "Unknown port")
        print(f"Device number {device}\t(port: {device_port})\t had {error_count} errors")

if __name__ == "__main__":
    restart_service()
    device_to_port, device_errors = parse_config_file("/mnt/data/etc/wb-mqtt-serial.conf")
    parse_journal(device_to_port, device_errors)
