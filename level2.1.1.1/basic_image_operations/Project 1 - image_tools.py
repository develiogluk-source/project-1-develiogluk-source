from PIL import Image
import numpy as np
import os


# -----------------------------
# 1) Görüntüyü okuma
# -----------------------------
def read_image(image_path):
    img = Image.open(image_path)
    return img


# -----------------------------
# 2) Grayscale'e çevirme
# -----------------------------
def convert_to_grayscale(img):
    return img.convert('L')


# -----------------------------
# 3) PIL -> NumPy array
# -----------------------------
def pil_to_np(img):
    return np.array(img)


# -----------------------------
# 4) Histogram hesaplama
# -----------------------------
def calculate_histogram(image_array):
    histogram = np.zeros(256)

    rows, cols = image_array.shape

    for i in range(rows):
        for j in range(cols):
            pixel_value = image_array[i][j]
            histogram[pixel_value] += 1

    return histogram


# -----------------------------
# 5) Olasılık hesaplama
# -----------------------------
def calculate_probabilities(histogram, total_pixels):
    probabilities = histogram / total_pixels
    return probabilities


# -----------------------------
# 6) Entropy hesaplama
# -----------------------------
def calculate_entropy(probabilities):
    entropy = 0

    for p in probabilities:
        if p > 0:  # log(0) hatasını önlemek için
            entropy += p * np.log2(p)

    return -entropy


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    # Çalıştığın klasörü al
    current_directory = os.path.dirname(os.path.realpath(__file__))

    # Test image yolu
    image_path = os.path.join(current_directory, "thumbs_up.bmp")

    # 1) Oku
    img = read_image(image_path)

    # 2) Grayscale yap
    gray_img = convert_to_grayscale(img)

    # 3) NumPy array'e çevir
    image_array = pil_to_np(gray_img)

    # Toplam piksel sayısı
    total_pixels = image_array.shape[0] * image_array.shape[1]

    # 4) Histogram
    histogram = calculate_histogram(image_array)

    # 5) Olasılıklar
    probabilities = calculate_probabilities(histogram, total_pixels)

    # 6) Entropy
    entropy = calculate_entropy(probabilities)

    print("Image size:", image_array.shape)
    print("Total pixels:", total_pixels)
    print("Entropy:", entropy, "bits/pixel")    