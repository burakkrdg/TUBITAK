import machine
import math
import time

class QMC5883P:
    def __init__(self, i2c, address=0x2c):
        self.i2c = i2c
        self.address = address
        self.init_sensor()

    def init_sensor(self):
        # QMC5883P Konfigürasyon Ayarları
        # 0x29 register: Periyodik set/reset açık
        self.i2c.writeto_mem(self.address, 0x29, b'\x06')
        # 0x0B register: Set/Reset periyodu ayarı
        self.i2c.writeto_mem(self.address, 0x0B, b'\x08')
        # 0x0A register: OSR=512, RNG=8G, ODR=200Hz, Sürekli Ölçüm Modu (Continuous)
        self.i2c.writeto_mem(self.address, 0x0A, b'\xCD')
        time.sleep(0.1)

    def read_raw_data(self):
        # QMC5883P'de veri 0x01 adresinden başlar: 
        # Sıralama: X_LSB, X_MSB, Y_LSB, Y_MSB, Z_LSB, Z_MSB
        try:
            data = self.i2c.readfrom_mem(self.address, 0x01, 6)
            
            x = self.convert_to_int(data[1], data[0])
            y = self.convert_to_int(data[3], data[2])
            z = self.convert_to_int(data[5], data[4])
            
            return x, y, z
        except OSError:
            # Okuma sırasında kablo temassızlığı olursa hata vermemesi için
            return 0, 0, 0

    def convert_to_int(self, msb, lsb):
        val = (msb << 8) | lsb
        if val >= 32768:
            val -= 65536
        return val

    def get_heading(self):
        x, y, z = self.read_raw_data()
        
        # X ve Y verileri sıfırsa (hata durumu) açıyı 0 döndür
        if x == 0 and y == 0:
            return 0.0
            
        # Pusula açısını hesapla (Radyan cinsinden)
        heading_rad = math.atan2(y, x)

        # Türkiye için yaklaşık manyetik sapma (Declination) eklentisi 
        # Bulunduğun konuma göre sapma yaklaşık +5.5 derece -> 0.096 radyan
        heading_rad += 0.096

        # Değeri 0 - 2*Pi (0-360 derece) aralığına sınırla
        if heading_rad < 0:
            heading_rad += 2 * math.pi
        if heading_rad > 2 * math.pi:
            heading_rad -= 2 * math.pi

        # Radyanı dereceye çevirerek döndür
        return heading_rad * (180.0 / math.pi)

# --- ANA KOD (ÇALIŞTIRMA KISMI) ---
if __name__ == '__main__':
    # ESP32 standart I2C pinleri: SDA=21, SCL=22
    i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21), freq=100000)

    print("Sensör başlatılıyor...")
    
    # 0x2c adresli QMC5883P nesnesini oluştur
    compass = QMC5883P(i2c, address=0x2c)
    time.sleep(1)
    
    print("Ölçüm başladı. Durdurmak için Ctrl+C yapın.\n" + "-"*40)

    while True:
        try:
            x, y, z = compass.read_raw_data()
            heading = compass.get_heading()
            
            print(f"Eksenler -> X: {x:6} | Y: {y:6} | Z: {z:6}  ||  Açı (Heading): {heading:.1f}°")
            time.sleep(0.2) # Saniyede 5 ölçüm
            
        except KeyboardInterrupt:
            print("\nÖlçüm kullanıcı tarafından durduruldu.")
            break
        except Exception as e:
            print("Beklenmeyen bir hata oluştu:", e)
            time.sleep(1)
