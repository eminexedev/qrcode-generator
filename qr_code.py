import segno

data = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

qr = segno.make(data, error="h")
qr.save("qr_code.png", scale=10, border=5)

print("QR code generated and saved as qr_code.png")