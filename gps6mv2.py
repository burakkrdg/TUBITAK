from machine import UART, Pin
from structures import TinyGPSPlus # Kütüphaneyi içe aktar
import time

# UART kurulumu
gps_uart = UART(2, baudrate=9600, tx=17, rx=16)
gps = TinyGPSPlus()

def get_gps_data():
    while gps_uart.any():
        byte = gps_uart.read(1)
        if byte:
            # Gelen her byte'ı kütüphaneye besle
            res = gps.update(byte[0])
            
    if gps.latitude.is_valid and gps.longitude.is_valid:
        print("-" * 20)
        print(f"Enlem: {gps.latitude.decimal}")
        print(f"Boylam: {gps.longitude.decimal}")
        print(f"Hız: {gps.speed.kmph} km/h")
        print(f"Uydu Sayısı: {gps.satellites.value}")
        print("-" * 20)
    else:
        print("Uydu aranıyor... Lütfen açık alana çıkın.")

while True:
    get_gps_data()
    time.sleep(2)