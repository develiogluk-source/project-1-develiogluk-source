from PIL import Image
import numpy as np
import os

# --- Fonksiyon Tanımlamaları ---

def read_image_from_file(img_file_path):
    return Image.open(img_file_path)

def write_compressed_image(img, img_file_path, quality=85):
    """
    Resmi kaydederken sıkıştırma uygular.
    BMP sıkıştırmayı desteklemediği için JPEG kullanmak en mantıklısıdır.
    """
    # Eğer dosya sonu .bmp ise ve sıkıştırma istiyorsak .jpg'ye çevirmek daha iyidir
    # Ama mutlaka .bmp kalacaksa, Pillow 'optimize' parametresini deneyebilir.
    if img_file_path.lower().endswith('.jpg') or img_file_path.lower().endswith('.jpeg'):
        img.save(img_file_path, 'JPEG', optimize=True, quality=quality)
    else:
        # BMP için gerçek bir sıkıştırma yoktur, ama optimize denenebilir
        img.save(img_file_path, 'bmp')

# --- Ana Program Akışı ---

current_directory = os.path.dirname(os.path.realpath(__file__))
input_file_path = os.path.join(current_directory, 'thumbs_up.bmp')

try:
    color_image = read_image_from_file(input_file_path)
    
    # 1. Gri tonlamaya çevir
    grayscale_image = color_image.convert('L')
    
    # 2. PROJE TAMAMLAMA VE SIKIŞTIRMA
    # Dosya boyutunu küçültmek için .jpg formatı ve %50 kalite seçtik
    output_file_path = os.path.join(current_directory, 'thumbs_up_compressed.jpg')
    
    # Quality değerini düşürdükçe dosya boyutu azalır (Örn: 20 çok küçük ama kalitesiz olur)
    grayscale_image.save(output_file_path, 'JPEG', optimize=True, quality=50)
    
    print(f"✅ İşlem Başarılı!")
    print(f"Orijinal Boyut: {os.path.getsize(input_file_path) // 1024} KB")
    print(f"Yeni Boyut: {os.path.getsize(output_file_path) // 1024} KB")
    print(f"📂 Kaydedilen dosya: {output_file_path}")

except Exception as e:
    print(f"❌ Hata: {e}")