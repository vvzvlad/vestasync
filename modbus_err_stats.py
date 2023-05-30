#!/usr/bin/env python3
import subprocess
import re
import os
import json
import argparse

def restart_service(history=False):
    if history == False:
        subprocess.Popen(["systemctl", "restart", "wb-mqtt-serial"], stdout=subprocess.PIPE)

def parse_config_file(filename):
    with open(filename, "r") as file:
        config_data = json.load(file)

    device_to_port = {}
    device_stats = {}
    for port in config_data["ports"]:
        for device in port["devices"]:
            device_to_port[device["slave_id"]] = port["path"]
            device_stats[device["slave_id"]] = {"type": device.get("device_type", "Unknown type"), "errors": 0, "disconnects": 0, "write_failures": 0}  # Initialize counts as zero

    return device_to_port, device_stats

def parse_journal(device_to_port, device_stats, history=False):
    cmd = ["journalctl", "-f", "-u", "wb-mqtt-serial"] if not history else ["journalctl", "-u", "wb-mqtt-serial"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    last_log_line = None

    for line in iter(p.stdout.readline, b''):
        line = line.decode('utf-8')  # convert bytes to string
        match_error = re.search(r'modbus:(\d+): Serial protocol error: request timed out', line)
        match_disconnect = re.search(r'INFO: \[serial device\] device modbus:(\d+) is disconnected', line)
        match_write_failure = re.search(r'WARNING: \[modbus\] failed to write: <modbus:(\d+):', line)
        if match_error:
            device_number = match_error.group(1)
            device_stats[device_number]["errors"] += 1
        elif match_disconnect:
            device_number = match_disconnect.group(1)
            device_stats[device_number]["disconnects"] += 1
        elif match_write_failure:
            device_number = match_write_failure.group(1)
            device_stats[device_number]["write_failures"] += 1

        last_log_line = line

        # clear the console
        os.system('clear')

        # print the last log line
        print(f"Last log line: {last_log_line}")

        # print error statistics
        print_error_statistics(device_stats, device_to_port)

def print_error_statistics(device_stats, device_to_port):
    print("\n--- Device Statistics ---")

    # sort by total count
    sorted_device_stats = sorted(device_stats.items(), key=lambda x: (x[1]["errors"], x[1]["disconnects"], x[1]["write_failures"]), reverse=True)

    max_type_length = max(len(stats['type']) for stats in device_stats.values())
    for device, stats in sorted_device_stats:
        device_port = device_to_port.get(device, "Unknown port")
        type_field = stats['type'].ljust(max_type_length)
        print(f"{type_field}\t {device}\t on port: {device_port},\t timeouts: {stats['errors']},\t disconnects: {stats['disconnects']},\t write failures: {stats['write_failures']}")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--history", help="parse historical data from journal", action="store_true")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    restart_service(history=args.history)
    device_to_port, device_stats = parse_config_file("/mnt/data/etc/wb-mqtt-serial.conf")
    parse_journal(device_to_port, device_stats, history=args.history)
