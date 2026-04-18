import machine
import time

# ESP32 standart I2C pinleri (Kendi bağlantına göre değiştirebilirsin)
SCL_PIN = 22
SDA_PIN = 21

def i2c_tara():
    # I2C nesnesini başlat (Frekans: 100kHz)
    i2c = machine.I2C(0, scl=machine.Pin(SCL_PIN), sda=machine.Pin(SDA_PIN), freq=100000)
    
    print("I2C Hat Taraması Başlatıldı...")
    print("Durdurmak için 'Ctrl+C' yapabilirsiniz.\n")
    print("-" * 40)
    
    while True:
        try:
            # Hattaki cihazları tara
            cihazlar = i2c.scan()
            
            if len(cihazlar) == 0:
                print("Cihaz bulunamadı! Bağlantıları (SDA, SCL, 3.3V, GND) kontrol et.")
            else:
                print(f"{len(cihazlar)} adet I2C cihazı bulundu:")
                for adres in cihazlar:
                    print(f" -> Hexadecimal: {hex(adres)} | Decimal: {adres}")
                    
            print("-" * 40)
            time.sleep(1)  # 1 saniye bekle ve tekrar tara
            
        except OSError as e:
            print("I2C Hatası (Kabloları kontrol et):", e)
            time.sleep(1)

# Kodu çalıştır
if __name__ == "__main__":
    i2c_tara()