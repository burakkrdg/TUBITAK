from machine import UART, Pin
import time

# UART2 konfigürasyonu (TX=17, RX=16)
gps_uart = UART(2, baudrate=9600, tx=17, rx=16)

print("GPS verisi bekleniyor...")

while True:
    if gps_uart.any():
        data = gps_uart.readline()
        print(data) # Ham NMEA verilerini terminale basar
    time.sleep(0.1)