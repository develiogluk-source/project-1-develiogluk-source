import os
import sys
import math
from PIL import Image
import numpy as np


class ImageLZWCompression:
    def __init__(self, input_path):
        self.input_path = os.path.abspath(input_path)
        self.current_directory = os.path.dirname(self.input_path) or os.getcwd()

        ext = os.path.splitext(self.input_path)[1].lower()
        file_name = os.path.basename(self.input_path)

        if ext in [".bmp", ".png", ".jpg", ".jpeg"]:
            self.image_path = self.input_path
            self.base_name = os.path.splitext(file_name)[0]
            self.compressed_path = os.path.join(self.current_directory, f"{self.base_name}_lzw_compressed.bin")
        elif ext == ".bin":
            self.compressed_path = self.input_path
            if file_name.endswith("_lzw_compressed.bin"):
                self.base_name = file_name[:-len("_lzw_compressed.bin")]
            else:
                self.base_name = os.path.splitext(file_name)[0]
            self.image_path = os.path.join(self.current_directory, f"{self.base_name}.bmp")
        else:
            raise ValueError("Unsupported input file type. Use an image file or .bin file.")

        self.grayscale_path = os.path.join(self.current_directory, f"{self.base_name}_grayscale.bmp")
        self.restored_path = os.path.join(self.current_directory, f"{self.base_name}_restored.bmp")

        self.original_size = 0
        self.compressed_size = 0
        self.code_length = 9
        self.avg_code_length = 0.0
        self.compression_ratio = 0.0
        self.entropy = 0.0

    # ------------------------------------------------------------
    # IMAGE UTILITIES
    # ------------------------------------------------------------

    def read_image(self):
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Image file not found: {self.image_path}")
        return Image.open(self.image_path)

    def convert_to_grayscale(self, img):
        return img.convert("L")

    def save_grayscale_image(self, gray_img):
        gray_img.save(self.grayscale_path)
        return self.grayscale_path

    def ensure_grayscale_exists(self):
        if os.path.exists(self.grayscale_path):
            return

        if not os.path.exists(self.image_path):
            return

        img = self.read_image()
        gray_img = self.convert_to_grayscale(img)
        self.save_grayscale_image(gray_img)

    def image_to_bytes_and_shape(self, gray_img):
        arr = np.array(gray_img, dtype=np.uint8)
        height, width = arr.shape
        return arr.tobytes(), width, height, arr

    # ------------------------------------------------------------
    # ENTROPY
    # ------------------------------------------------------------

    def calculate_entropy(self, image_array):
        flat = image_array.flatten()
        histogram = np.bincount(flat, minlength=256)
        total_pixels = flat.size

        if total_pixels == 0:
            self.entropy = 0.0
            return 0.0

        probabilities = histogram / total_pixels

        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log2(p)

        self.entropy = entropy
        return entropy

    # ------------------------------------------------------------
    # LZW CORE
    # ------------------------------------------------------------

    def lzw_compress(self, data_bytes):
        if not data_bytes:
            return []

        dict_size = 256
        dictionary = {bytes([i]): i for i in range(dict_size)}

        w = bytes([data_bytes[0]])
        codes = []

        for byte in data_bytes[1:]:
            c = bytes([byte])
            wc = w + c

            if wc in dictionary:
                w = wc
            else:
                codes.append(dictionary[w])
                dictionary[wc] = dict_size
                dict_size += 1
                w = c

        codes.append(dictionary[w])
        return codes

    def lzw_decompress(self, codes):
        if not codes:
            return b""

        dict_size = 256
        dictionary = {i: bytes([i]) for i in range(dict_size)}

        if codes[0] not in dictionary:
            raise ValueError("Invalid compressed data: first code is not valid.")

        w = dictionary[codes[0]]
        result = bytearray(w)

        for k in codes[1:]:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dict_size:
                entry = w + w[:1]
            else:
                raise ValueError(f"Bad compressed code: {k}")

            result.extend(entry)
            dictionary[dict_size] = w + entry[:1]
            dict_size += 1
            w = entry

        return bytes(result)

    # ------------------------------------------------------------
    # BIT PACKING
    # ------------------------------------------------------------

    def calculate_code_length(self, codes):
        if not codes:
            return 9
        return max(9, max(codes).bit_length())

    def int_array_to_binary_string(self, int_array, code_length):
        return "".join(format(num, f"0{code_length}b") for num in int_array)

    def pad_encoded_text(self, encoded_text):
        extra_padding = (8 - len(encoded_text) % 8) % 8
        encoded_text += "0" * extra_padding
        padded_info = format(extra_padding, "08b")
        return padded_info + encoded_text

    def get_byte_array(self, padded_encoded_text):
        if len(padded_encoded_text) % 8 != 0:
            raise ValueError("Encoded text not padded properly.")

        b = bytearray()
        for i in range(0, len(padded_encoded_text), 8):
            b.append(int(padded_encoded_text[i:i + 8], 2))
        return b

    def remove_padding(self, padded_encoded_text, code_length):
        if len(padded_encoded_text) < 8:
            raise ValueError("Compressed data is too short.")

        padded_info = padded_encoded_text[:8]
        extra_padding = int(padded_info, 2)
        encoded_text = padded_encoded_text[8:]

        if extra_padding > 0:
            encoded_text = encoded_text[:-extra_padding]

        codes = []
        for i in range(0, len(encoded_text), code_length):
            chunk = encoded_text[i:i + code_length]
            if len(chunk) == code_length:
                codes.append(int(chunk, 2))

        return codes

    # ------------------------------------------------------------
    # FILE FORMAT
    # Header:
    # 4 bytes width
    # 4 bytes height
    # 1 byte code_length
    # remaining bytes = packed LZW data
    # ------------------------------------------------------------

    def write_compressed_file(self, width, height, code_length, byte_array):
        with open(self.compressed_path, "wb") as f:
            f.write(width.to_bytes(4, byteorder="big"))
            f.write(height.to_bytes(4, byteorder="big"))
            f.write(bytes([code_length]))
            f.write(byte_array)

    def read_compressed_file(self):
        if not os.path.exists(self.compressed_path):
            raise FileNotFoundError(f"Compressed file not found: {self.compressed_path}")

        with open(self.compressed_path, "rb") as f:
            width = int.from_bytes(f.read(4), byteorder="big")
            height = int.from_bytes(f.read(4), byteorder="big")
            code_length_byte = f.read(1)
            if not code_length_byte:
                raise ValueError("Compressed file is corrupted.")
            code_length = code_length_byte[0]
            raw_bytes = f.read()

        return width, height, code_length, raw_bytes

    # ------------------------------------------------------------
    # METRICS
    # ------------------------------------------------------------

    def calculate_metrics(self, original_data_len, codes, bitstring_len):
        self.original_size = original_data_len
        self.compressed_size = os.path.getsize(self.compressed_path)
        self.code_length = self.calculate_code_length(codes)

        if len(codes) > 0:
            self.avg_code_length = bitstring_len / len(codes)
        else:
            self.avg_code_length = 0.0

        if self.original_size > 0:
            self.compression_ratio = self.compressed_size / self.original_size
        else:
            self.compression_ratio = 0.0

    # ------------------------------------------------------------
    # COMPARE
    # ------------------------------------------------------------

    def compare_images(self, original_gray_array, restored_array):
        same_shape = original_gray_array.shape == restored_array.shape
        same_pixels = np.array_equal(original_gray_array, restored_array)
        return same_shape and same_pixels

    # ------------------------------------------------------------
    # MAIN PIPELINES
    # ------------------------------------------------------------

    def compress(self):
        img = self.read_image()
        gray_img = self.convert_to_grayscale(img)
        self.save_grayscale_image(gray_img)

        data_bytes, width, height, gray_array = self.image_to_bytes_and_shape(gray_img)

        self.calculate_entropy(gray_array)

        codes = self.lzw_compress(data_bytes)
        code_length = self.calculate_code_length(codes)
        bitstring = self.int_array_to_binary_string(codes, code_length)
        padded = self.pad_encoded_text(bitstring)
        byte_array = self.get_byte_array(padded)

        self.write_compressed_file(width, height, code_length, byte_array)
        self.calculate_metrics(len(data_bytes), codes, len(bitstring))

        print("--------------------------------------------------")
        print("LEVEL 2 - IMAGE COMPRESSION")
        print("--------------------------------------------------")
        print(f"Original image: {os.path.basename(self.image_path)}")
        print(f"Grayscale image saved: {os.path.basename(self.grayscale_path)}")
        print(f"Compressed file saved: {os.path.basename(self.compressed_path)}")
        print(f"Image size: {width} x {height}")
        print(f"Original Size: {self.original_size} bytes")
        print(f"Compressed Size: {self.compressed_size} bytes")
        print(f"Entropy: {self.entropy:.4f} bits/pixel")
        print(f"Code Length: {code_length}")
        print(f"Average Code Length: {self.avg_code_length:.4f} bits/code")
        print(f"Compression Ratio: {self.compression_ratio:.4f}")

    def decompress(self):
        width, height, code_length, raw_bytes = self.read_compressed_file()

        bitstring = "".join(format(byte, "08b") for byte in raw_bytes)
        codes = self.remove_padding(bitstring, code_length)
        restored_bytes = self.lzw_decompress(codes)

        expected_size = width * height
        if len(restored_bytes) != expected_size:
            raise ValueError(
                f"Restored byte count does not match image size. "
                f"Expected {expected_size}, got {len(restored_bytes)}"
            )

        restored_array = np.frombuffer(restored_bytes, dtype=np.uint8).reshape((height, width))
        restored_img = Image.fromarray(restored_array, mode="L")
        restored_img.save(self.restored_path)

        is_identical = None
        self.ensure_grayscale_exists()

        if os.path.exists(self.grayscale_path):
            original_gray = Image.open(self.grayscale_path).convert("L")
            original_gray_array = np.array(original_gray, dtype=np.uint8)
            is_identical = self.compare_images(original_gray_array, restored_array)

        print("--------------------------------------------------")
        print("LEVEL 2 - IMAGE DECOMPRESSION")
        print("--------------------------------------------------")
        print(f"Compressed file read: {os.path.basename(self.compressed_path)}")
        print(f"Restored image saved: {os.path.basename(self.restored_path)}")
        print(f"Restored image size: {width} x {height}")

        if is_identical is None:
            print("Original vs Restored: COMPARISON SKIPPED")
        else:
            print(f"Original vs Restored: {'IDENTICAL' if is_identical else 'DIFFERENT'}")

        return is_identical

    def run_all(self):
        self.compress()
        self.decompress()


if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.realpath(__file__))

    mode = "all"
    input_path = os.path.join(current_directory, "thumbs_up.bmp")

    if len(sys.argv) >= 2:
        mode = sys.argv[1].strip().lower()

    if len(sys.argv) >= 3:
        input_path = sys.argv[2]

    processor = ImageLZWCompression(input_path)

    if mode == "compress":
        processor.compress()
    elif mode == "decompress":
        processor.decompress()
    else:
        processor.run_all()