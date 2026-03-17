import os
import math
from io import StringIO

import numpy as np
from PIL import Image


def read_image(image_path):
    return Image.open(image_path)


def convert_to_grayscale(img):
    return img.convert('L')


def pil_to_np(img):
    return np.array(img)


def np_to_pil(img_array):
    return Image.fromarray(np.uint8(img_array))


def flatten_image(image_array):
    return image_array.flatten().tolist()


def reshape_image(pixel_list, shape):
    return np.array(pixel_list, dtype=np.int16).reshape(shape)


def create_difference_image(image_array):
    rows, cols = image_array.shape
    diff_array = np.zeros((rows, cols), dtype=np.int16)

    diff_array[0, 0] = int(image_array[0, 0])

    for j in range(1, cols):
        diff_array[0, j] = int(image_array[0, j]) - int(image_array[0, j - 1])

    for i in range(1, rows):
        diff_array[i, 0] = int(image_array[i, 0]) - int(image_array[i - 1, 0])

    for i in range(1, rows):
        for j in range(1, cols):
            diff_array[i, j] = int(image_array[i, j]) - int(image_array[i, j - 1])

    return diff_array


def reconstruct_from_difference(diff_array):
    rows, cols = diff_array.shape
    restored = np.zeros((rows, cols), dtype=np.int16)

    restored[0, 0] = diff_array[0, 0]

    for j in range(1, cols):
        restored[0, j] = restored[0, j - 1] + diff_array[0, j]

    for i in range(1, rows):
        restored[i, 0] = restored[i - 1, 0] + diff_array[i, 0]

    for i in range(1, rows):
        for j in range(1, cols):
            restored[i, j] = restored[i, j - 1] + diff_array[i, j]

    return restored


def difference_to_displayable(diff_array):
    display_array = diff_array + 255
    display_array = np.clip(display_array, 0, 255)
    return display_array.astype(np.uint8)


def shift_difference_values(diff_array):
    return diff_array + 255


def unshift_difference_values(shifted_diff_array):
    return shifted_diff_array - 255


def lzw_encode_difference(values):
    dict_size = 511
    dictionary = {(i,): i for i in range(dict_size)}

    w = ()
    result = []

    for value in values:
        k = (int(value),)
        wk = w + k

        if wk in dictionary:
            w = wk
        else:
            result.append(dictionary[w])
            dictionary[wk] = dict_size
            dict_size += 1
            w = k

    if w:
        result.append(dictionary[w])

    code_length = math.ceil(math.log2(len(dictionary)))
    return result, code_length, len(dictionary)


def lzw_decode_difference(encoded_values):
    dict_size = 511
    dictionary = {i: (i,) for i in range(dict_size)}

    if not encoded_values:
        return []

    first_code = encoded_values[0]
    w = dictionary[first_code]
    decoded_values = list(w)

    for k in encoded_values[1:]:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            entry = w + (w[0],)
        else:
            raise ValueError(f"Bad compressed k: {k}")

        decoded_values.extend(entry)
        dictionary[dict_size] = w + (entry[0],)
        dict_size += 1
        w = entry

    return decoded_values


def int_list_to_binary_string(int_list, code_length):
    bits = []
    for num in int_list:
        for n in range(code_length):
            if num & (1 << (code_length - 1 - n)):
                bits.append('1')
            else:
                bits.append('0')
    return ''.join(bits)


def add_metadata(bitstring, width, height, code_length):
    width_bits = f"{width:016b}"
    height_bits = f"{height:016b}"
    code_length_bits = f"{code_length:08b}"
    return width_bits + height_bits + code_length_bits + bitstring


def pad_encoded_data(encoded_data):
    if len(encoded_data) % 8 != 0:
        extra_bits = 8 - (len(encoded_data) % 8)
        encoded_data += '0' * extra_bits
    else:
        extra_bits = 0

    padding_info = f"{extra_bits:08b}"
    return padding_info + encoded_data


def get_byte_array(padded_encoded_data):
    if len(padded_encoded_data) % 8 != 0:
        raise ValueError("Encoded data is not padded properly.")

    b = bytearray()
    for i in range(0, len(padded_encoded_data), 8):
        byte = padded_encoded_data[i:i + 8]
        b.append(int(byte, 2))
    return b


def remove_padding(bitstring):
    padding_info = bitstring[:8]
    encoded_data = bitstring[8:]
    extra_padding = int(padding_info, 2)

    if extra_padding != 0:
        encoded_data = encoded_data[:-extra_padding]

    return encoded_data


def extract_metadata(bitstring):
    width = int(bitstring[:16], 2)
    height = int(bitstring[16:32], 2)
    code_length = int(bitstring[32:40], 2)
    remaining_bits = bitstring[40:]
    return width, height, code_length, remaining_bits


def binary_string_to_int_list(bitstring, code_length):
    int_codes = []
    for i in range(0, len(bitstring), code_length):
        chunk = bitstring[i:i + code_length]
        if len(chunk) == code_length:
            int_codes.append(int(chunk, 2))
    return int_codes


def calculate_histogram(image_array):
    histogram = np.zeros(511, dtype=int)
    rows, cols = image_array.shape

    for i in range(rows):
        for j in range(cols):
            histogram[image_array[i][j]] += 1

    return histogram


def calculate_probabilities(histogram, total_pixels):
    return histogram / total_pixels


def calculate_entropy(probabilities):
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy += p * np.log2(p)
    return -entropy


def calculate_average_code_length(code_length):
    return float(code_length)


def compress_difference_image_file(input_path, output_bin_path, diff_image_path):
    img = read_image(input_path)
    gray_img = convert_to_grayscale(img)
    image_array = pil_to_np(gray_img)

    diff_array = create_difference_image(image_array)

    diff_display = difference_to_displayable(diff_array)
    np_to_pil(diff_display).save(diff_image_path)

    shifted_diff = shift_difference_values(diff_array)
    shifted_list = flatten_image(shifted_diff)

    encoded_output, code_length, dictionary_size = lzw_encode_difference(shifted_list)

    height, width = shifted_diff.shape

    bitstring = int_list_to_binary_string(encoded_output, code_length)
    bitstring = add_metadata(bitstring, width, height, code_length)
    padded_bitstring = pad_encoded_data(bitstring)
    byte_array = get_byte_array(padded_bitstring)

    with open(output_bin_path, 'wb') as f:
        f.write(bytes(byte_array))

    original_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(output_bin_path)
    compression_ratio = compressed_size / original_size if original_size != 0 else 0

    histogram = calculate_histogram(shifted_diff)
    probabilities = calculate_probabilities(histogram, shifted_diff.size)
    entropy = calculate_entropy(probabilities)
    average_code_length = calculate_average_code_length(code_length)

    print("Compression completed.")
    print("Original image shape:", image_array.shape)
    print("Difference image shape:", diff_array.shape)
    print("Difference min value:", diff_array.min())
    print("Difference max value:", diff_array.max())
    print("Shifted difference min:", shifted_diff.min())
    print("Shifted difference max:", shifted_diff.max())
    print("Encoded output length:", len(encoded_output))
    print("Dictionary size:", dictionary_size)
    print("Code length:", code_length)
    print("Original Size:", original_size, "bytes")
    print("Compressed Size:", compressed_size, "bytes")
    print(f"Compression Ratio (CR): {compression_ratio:.4f}")
    print(f"Entropy: {entropy:.4f} bits/pixel")
    print(f"Average Code Length: {average_code_length:.4f} bits/code")
    print("Difference image saved as:", diff_image_path)
    print("Compressed file saved as:", output_bin_path)


def decompress_difference_image_file(input_bin_path, restored_image_path):
    with open(input_bin_path, 'rb') as f:
        compressed_data = f.read()

    bit_string = StringIO()
    for byte in compressed_data:
        bits = bin(byte)[2:].rjust(8, '0')
        bit_string.write(bits)

    bit_string = bit_string.getvalue()
    bit_string = remove_padding(bit_string)
    width, height, code_length, encoded_bits = extract_metadata(bit_string)

    encoded_values = binary_string_to_int_list(encoded_bits, code_length)
    decoded_shifted_list = lzw_decode_difference(encoded_values)

    decoded_shifted_array = reshape_image(decoded_shifted_list, (height, width))
    decoded_diff_array = unshift_difference_values(decoded_shifted_array)

    restored_array = reconstruct_from_difference(decoded_diff_array)
    restored_array_uint8 = np.clip(restored_array, 0, 255).astype(np.uint8)

    np_to_pil(restored_array_uint8).save(restored_image_path)

    print("Decompression completed.")
    print("Restored image shape:", restored_array_uint8.shape)
    print("Restored image saved as:", restored_image_path)

    return restored_array_uint8


if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.realpath(__file__))

    input_image_path = os.path.join(current_directory, "thumbs_up.bmp")
    diff_image_path = os.path.join(current_directory, "thumbs_up_difference.bmp")
    compressed_bin_path = os.path.join(current_directory, "thumbs_up_difference_lzw_compressed.bin")
    restored_image_path = os.path.join(current_directory, "thumbs_up_difference_restored.bmp")

    print("Input path:", input_image_path)
    print("File exists:", os.path.exists(input_image_path))

    compress_difference_image_file(input_image_path, compressed_bin_path, diff_image_path)
    restored_array = decompress_difference_image_file(compressed_bin_path, restored_image_path)

    original_img = read_image(input_image_path)
    original_gray = convert_to_grayscale(original_img)
    original_array = pil_to_np(original_gray)

    same = np.array_equal(original_array, restored_array)
    print("Original and restored images are the same:", same)