#!/usr/bin/env python3
import subprocess
import re
import os
import json
import argparse

def restart_service(skip_restart=False, history=False):
    if not skip_restart and not history:
        subprocess.Popen(["systemctl", "restart", "wb-mqtt-serial"], stdout=subprocess.PIPE)

def parse_config_file(filename):
    with open(filename, "r") as file:
        config_data = json.load(file)

    device_to_port = {}
    device_stats = {}
    for port in config_data["ports"]:
        for device in port["devices"]:
            device_to_port[device["slave_id"]] = port["path"]
            device_stats[device["slave_id"]] = {"type": device.get("device_type", "Unknown type"), "errors": 0, "disconnects": 0, "write_failures": 0, "invalid_crc_errors": 0}  # New line

    return device_to_port, device_stats


def parse_journal(device_to_port, device_stats, skip_lines=10, history=False):
    cmd = ["journalctl", "-f", "-u", "wb-mqtt-serial"] if not history else ["journalctl", "-u", "wb-mqtt-serial"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    last_log_line = None
    line_counter = 0

    for line in iter(p.stdout.readline, b''):
        line_counter += 1
        if line_counter <= skip_lines:
            continue

        line = line.decode('utf-8')  # convert bytes to string
        match_error = re.search(r'modbus:(\d+): Serial protocol error: request timed out', line)
        match_disconnect = re.search(r'INFO: \[serial device\] device modbus:(\d+) is disconnected', line)
        match_write_failure = re.search(r'WARNING: \[modbus\] failed to write: <modbus:(\d+):', line)
        match_invalid_crc = re.search(r'modbus:(\d+): Serial protocol error: malformed response: invalid crc', line)  # New line
        if match_error:
            device_number = match_error.group(1)
            device_stats[device_number]["errors"] += 1
        elif match_disconnect:
            device_number = match_disconnect.group(1)
            device_stats[device_number]["disconnects"] += 1
        elif match_write_failure:
            device_number = match_write_failure.group(1)
            device_stats[device_number]["write_failures"] += 1
        elif match_invalid_crc:  # New line
            device_number = match_invalid_crc.group(1)
            device_stats[device_number]["invalid_crc_errors"] += 1  # New line

        last_log_line = line

        os.system('clear')

        print(f"Last log line: {last_log_line}")

        print_error_statistics(device_stats, device_to_port)


def print_table(headers, data):
    col_widths = [
        max(len(str(x)) for x in col)
        for col in zip(*data, headers)
    ]

    row_format = "| " + " | ".join("{:<" + str(width) + "}" for width in col_widths) + " |"
    print("+-" + "-+-".join("-" * width for width in col_widths) + "-+")
    print(row_format.format(*headers))
    print("+-" + "-+-".join("-" * width for width in col_widths) + "-+")

    for row in data:
        print(row_format.format(*row))
    print("+-" + "-+-".join("-" * width for width in col_widths) + "-+")


def print_error_statistics(device_stats, device_to_port):
    print("\n--- Error Statistics ---")
    sorted_device_stats = sorted(device_stats.items(), key=lambda x: (x[1]["errors"], x[1]["disconnects"], x[1]["write_failures"], x[1]["invalid_crc_errors"]), reverse=True)
    headers = ["Type", "Port", "ID", "Timeouts", "Disconnects", "Write Failures", "CRC Errors"]
    data = []

    for device, stats in sorted_device_stats:
        device_port = device_to_port.get(device, "Unknown port").replace("/dev/tty", "")
        type_field = stats['type']
        error_field = str(stats['errors'])
        disconnect_field = str(stats['disconnects'])
        write_failure_field = str(stats['write_failures'])
        invalid_crc_errors_field = str(stats['invalid_crc_errors'])
        data.append([type_field, device_port, device, error_field, disconnect_field, write_failure_field, invalid_crc_errors_field])

    print_table(headers, data)





def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--history", help="parse historical data from journal", action="store_true")
    parser.add_argument("-S", "--skip-service-restart", help="skip service restart", action="store_true")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    restart_service(skip_restart=args.skip_service_restart, history=args.history)
    device_to_port, device_stats = parse_config_file("/mnt/data/etc/wb-mqtt-serial.conf")
    parse_journal(device_to_port, device_stats, history=args.history)
