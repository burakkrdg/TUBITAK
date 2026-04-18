import machine
import time
import mlx90640
import gc

# ESP32 için varsayılan I2C pin yapılandırması
# Donanımınıza göre GPIO pinlerini değiştirebilirsiniz (Örn: SCL=22, SDA=21)
SCL_PIN = 22
SDA_PIN = 21

# I2C veriyolunu başlat
i2c = machine.SoftI2C(scl=machine.Pin(SCL_PIN), sda=machine.Pin(SDA_PIN), freq=400000)

print("I2C cihazları taranıyor...")
devices = i2c.scan()
if devices:
    for d in devices:
        print(f"I2C cihazı bulundu, adres: 0x{d:02X}")
else:
    print("I2C cihazı bulunamadı! Lütfen kablo bağlantılarını kontrol edin.")

try:
    print("MLX90640 sensörü başlatılıyor...")
    # Sensör nesnesini oluştur (varsayılan adres: 0x33)
    mlx = mlx90640.MLX90640(i2c)
    
    # Yenileme hızını ayarla (Örn: 2Hz)
    mlx.refresh_rate = mlx90640.RefreshRate.REFRESH_2_HZ
    
    # 32x24 çözünürlük için 768 elemanlı boş bir liste (frame) oluştur
    frame = [0.0] * 768
    
    print("Okuma başlatıldı...")
    
    while True:
        try:
            # Belleği temizle
            gc.collect()
            
            # Görüntü (frame) verisini sensörden oku
            mlx.get_frame(frame)
            
            # Merkez, minimum ve maksimum sıcaklıkları bul
            center_temp = frame[12 * 32 + 16] # Yaklaşık merkezdeki piksel (12. satır, 16. sütun)
            min_temp = min(frame)
            max_temp = max(frame)
            
            print(f"Merkez: {center_temp:.1f}°C | Min: {min_temp:.1f}°C | Max: {max_temp:.1f}°C")
            
        except ValueError:
            # Okuma sırasında anlık veri kayıpları/hataları yaşanabilir, yoksay ve devam et
            print("Veri okuma hatası, tekrar deneniyor...")
            
        time.sleep(0.5)

except Exception as e:
    print(f"Hata oluştu: {e}")
