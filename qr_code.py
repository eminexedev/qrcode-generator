import segno

# Örnek amaçlı sabit veri: bu script tek başına çalıştırıldığında QR üretir.
data = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Hata düzeltme seviyesi yüksek olacak şekilde QR nesnesi oluşturulur.
qr = segno.make(data, error="h")
# QR dosyasını png formatında kaydeder.
qr.save("qr_code.png", scale=10, border=5)

print("QR code generated and saved as qr_code.png")