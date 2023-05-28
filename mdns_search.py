#!/usr/bin/env python3
import sys
import time
from zeroconf import ServiceBrowser, Zeroconf
from threading import Event

class MyListener:

    def __init__(self):
        self.found_services = []

    def remove_service(self, zeroconf, type, name):
        pass

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        self.found_services.append(info)
        print(f"Name: {info.name}")
        print(f"IP: {info.parsed_addresses()[0]}")
        print("")

    def update_service(self, zeroconf, type, name):
        pass

def main():
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, "_workstation._tcp.local.", listener)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        browser.cancel()
        zeroconf.close()

if __name__ == "__main__":
    main()
