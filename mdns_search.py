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

    def update_service(self, zeroconf, type, name):
        pass

def main():
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, "_workstation._tcp.local.", listener)

    # Устанавливаем время ожидания и ждем, пока не найдутся все службы
    timeout = 15
    wait_event = Event()
    wait_event.wait(timeout)

    # Закрываем браузер служб и освобождаем ресурсы
    browser.cancel()
    zeroconf.close()

    # Выводим список найденных служб
    print("Found services:")
    for service in listener.found_services:
        print(f"Name: {service.name}")
        print(f"IP: {service.parsed_addresses()[0]}")
        print("")

if __name__ == "__main__":
    main()




