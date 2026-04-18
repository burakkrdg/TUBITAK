import machine
from machine import UART, Pin
import time
import network
import socket
import mlx90640
import gc
import struct

# ─── GPS Kurulumu ──────────────────────────────────────
gps_uart = UART(2, baudrate=9600, tx=17, rx=16)
# ───────────────────────────────────────────────────────

# ─── WiFi Ayarları ─────────────────────────────────────
WIFI_SSID = "FiberHGW_ZTC27G"
WIFI_PASS = "bXDzFb4XuYH4"
SERVER_IP = "10.64.32.24"
SERVER_PORT = 5006
# ───────────────────────────────────────────────────────

SCL_PIN = 22
SDA_PIN = 21

FRAME_SIZE = 768
CHUNK_SIZE = 128
CHUNKS = 6
# 258 byte Termal + 8 byte GPS (2 adet 32-bit float: enlem, boylam) = 266 byte
CHUNK_BUF = bytearray(2 + CHUNK_SIZE * 2 + 8)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("WiFi: " + WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASS)
        t = 20
        while not wlan.isconnected() and t > 0:
            time.sleep(1)
            t -= 1
    if wlan.isconnected():
        print("WiFi OK: " + wlan.ifconfig()[0])
        return True
    print("WiFi HATA!")
    return False


def main():
    if not connect_wifi():
        return

    i2c = machine.SoftI2C(scl=machine.Pin(SCL_PIN), sda=machine.Pin(SDA_PIN), freq=400000)
    for d in i2c.scan():
        print("I2C: 0x{:02X}".format(d))

    gc.collect()
    gc.threshold(4096)  # Agresif GC - her 4KB allokasyonda tetikle
    print("MLX90640 init...")
    mlx = mlx90640.MLX90640(i2c)
    mlx.refresh_rate = mlx90640.RefreshRate.REFRESH_2_HZ

    frame = [0.0] * FRAME_SIZE

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (SERVER_IP, SERVER_PORT)

    gc.collect()
    print("mem: {}".format(gc.mem_free()))

    # Warmup
    try:
        gc.collect()
        mlx.get_frame(frame)
        gc.collect()
        mlx.get_frame(frame)
        gc.collect()
    except:
        gc.collect()

    print("Basliyor!")
    n = 0
    lat = 0.0
    lon = 0.0

    while True:
        # 0. GPS Verisini (Ham NMEA) Oku ve Güncelle
        while gps_uart.any():
            try:
                line = gps_uart.readline()
                if line:
                    decoded = line.decode('ascii', 'ignore')
                    if decoded.startswith('$GPRMC') or decoded.startswith('$GPGGA'):
                        parts = decoded.split(',')
                        
                        _lat_str = None
                        _lat_dir = None
                        _lon_str = None
                        _lon_dir = None
                        
                        if parts[0] == '$GPRMC' and len(parts) >= 7 and parts[2] == 'A':
                            _lat_str, _lat_dir, _lon_str, _lon_dir = parts[3], parts[4], parts[5], parts[6]
                        elif parts[0] == '$GPGGA' and len(parts) >= 7 and parts[6] not in ('0', ''):
                            _lat_str, _lat_dir, _lon_str, _lon_dir = parts[2], parts[3], parts[4], parts[5]
                            
                        if _lat_str and _lon_str:
                            idx1 = _lat_str.find('.')
                            idx2 = _lon_str.find('.')
                            if idx1 >= 2 and idx2 >= 2:
                                deg1 = float(_lat_str[:idx1-2])
                                min1 = float(_lat_str[idx1-2:])
                                new_lat = deg1 + (min1 / 60.0)
                                if _lat_dir == 'S': new_lat = -new_lat
                                
                                deg2 = float(_lon_str[:idx2-2])
                                min2 = float(_lon_str[idx2-2:])
                                new_lon = deg2 + (min2 / 60.0)
                                if _lon_dir == 'W': new_lon = -new_lon
                                
                                lat = new_lat
                                lon = new_lon
            except Exception:
                pass

        # 1. Tam GC
        gc.collect()
        mem_before = gc.mem_free()

        # 2. Sensör oku (TEK çağrı)
        try:
            mlx.get_frame(frame)
        except ValueError:
            gc.collect()
            time.sleep_ms(200)
            continue
        except MemoryError:
            gc.collect()
            time.sleep(1)
            print("ME! m:{}".format(gc.mem_free()))
            continue

        # 3. GC - get_frame'in temp objelerini temizle
        gc.collect()

        # 4. Chunk gönder
        for chunk_id in range(CHUNKS):
            CHUNK_BUF[0] = 0xAA
            CHUNK_BUF[1] = chunk_id

            base = chunk_id * CHUNK_SIZE
            for j in range(CHUNK_SIZE):
                val = int(frame[base + j] * 10)
                if val < 0:
                    val += 65536
                off = 2 + j * 2
                CHUNK_BUF[off] = (val >> 8) & 0xFF
                CHUNK_BUF[off + 1] = val & 0xFF

            # GPS verisini (8 byte) paketin sonuna paketle: Little-Endian float
            try:
                gps_bytes = struct.pack('<ff', lat, lon)
                CHUNK_BUF[258:266] = gps_bytes
            except Exception:
                pass

            try:
                sock.sendto(CHUNK_BUF, addr)
                print(CHUNK_BUF)
            except OSError:
                gc.collect()
                time.sleep_ms(100)
                try:
                    sock.sendto(CHUNK_BUF, addr)
                except:
                    pass

            time.sleep_ms(10)

        # 5. Log
        n += 1
        gc.collect()
        if n % 5 == 0:
            print("f:{} m:{}({})".format(n, gc.mem_free(), mem_before))

        # 6. Frame arası bekleme - sensör ve GC'ye zaman ver
        time.sleep_ms(300)


main()
