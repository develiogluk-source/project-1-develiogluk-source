import os
import math
import numpy as np
from PIL import Image


def read_image(image_path):
    return Image.open(image_path)


def pil_to_np(img):
    return np.array(img)


def np_to_pil(img_array):
    return Image.fromarray(np.uint8(img_array))


def split_rgb_channels(image_array):
    red = image_array[:, :, 0]
    green = image_array[:, :, 1]
    blue = image_array[:, :, 2]
    return red, green, blue


def merge_rgb_channels(red, green, blue):
    return np.stack([red, green, blue], axis=2)


def flatten_channel(channel_array):
    return channel_array.flatten().tolist()


def reshape_channel(pixel_list, shape):
    return np.array(pixel_list, dtype=np.int16).reshape(shape)


def save_channel_image(channel_array, output_path):
    np_to_pil(channel_array).save(output_path)


def create_difference_image(channel_array):
    rows, cols = channel_array.shape
    diff_array = np.zeros((rows, cols), dtype=np.int16)

    diff_array[0, 0] = int(channel_array[0, 0])

    for j in range(1, cols):
        diff_array[0, j] = int(channel_array[0, j]) - int(channel_array[0, j - 1])

    for i in range(1, rows):
        diff_array[i, 0] = int(channel_array[i, 0]) - int(channel_array[i - 1, 0])

    for i in range(1, rows):
        for j in range(1, cols):
            diff_array[i, j] = int(channel_array[i, j]) - int(channel_array[i, j - 1])

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
            if w:
                result.append(dictionary[w])
            dictionary[wk] = dict_size
            dict_size += 1
            w = k

    if w:
        result.append(dictionary[w])

    code_length = max(9, math.ceil(math.log2(len(dictionary))))
    return result, code_length, len(dictionary)


def lzw_decode_difference(encoded_values):
    dict_size = 511
    dictionary = {i: (i,) for i in range(dict_size)}

    if not encoded_values:
        return []

    first_code = encoded_values[0]
    if first_code not in dictionary:
        raise ValueError("First LZW code is invalid.")

    w = dictionary[first_code]
    decoded_values = list(w)

    for k in encoded_values[1:]:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            entry = w + (w[0],)
        else:
            raise ValueError(f"Bad compressed code: {k}")

        decoded_values.extend(entry)
        dictionary[dict_size] = w + (entry[0],)
        dict_size += 1
        w = entry

    return decoded_values


def int_list_to_binary_string(int_list, code_length):
    return ''.join(format(num, f'0{code_length}b') for num in int_list)


def add_metadata(bitstring, width, height, code_length):
    width_bits = f"{width:016b}"
    height_bits = f"{height:016b}"
    code_length_bits = f"{code_length:08b}"
    return width_bits + height_bits + code_length_bits + bitstring


def pad_encoded_data(encoded_data):
    extra_bits = (8 - (len(encoded_data) % 8)) % 8
    encoded_data += '0' * extra_bits
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


def calculate_histogram(channel_array):
    return np.bincount(channel_array.flatten(), minlength=511)


def calculate_probabilities(histogram, total_pixels):
    return histogram / total_pixels


def calculate_entropy(probabilities):
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * np.log2(p)
    return entropy


def compress_difference_channel(channel_array, output_bin_path, diff_image_path, channel_name):
    diff_array = create_difference_image(channel_array)

    diff_display = difference_to_displayable(diff_array)
    np_to_pil(diff_display).save(diff_image_path)

    shifted_diff = shift_difference_values(diff_array)
    shifted_list = flatten_channel(shifted_diff)

    encoded_output, code_length, dictionary_size = lzw_encode_difference(shifted_list)

    height, width = shifted_diff.shape

    bitstring_only_codes = int_list_to_binary_string(encoded_output, code_length)
    full_bitstring = add_metadata(bitstring_only_codes, width, height, code_length)
    padded_bitstring = pad_encoded_data(full_bitstring)
    byte_array = get_byte_array(padded_bitstring)

    with open(output_bin_path, 'wb') as f:
        f.write(bytes(byte_array))

    compressed_size = os.path.getsize(output_bin_path)

    histogram = calculate_histogram(shifted_diff)
    probabilities = calculate_probabilities(histogram, shifted_diff.size)
    entropy = calculate_entropy(probabilities)

    if len(encoded_output) > 0:
        average_code_length = len(bitstring_only_codes) / len(encoded_output)
    else:
        average_code_length = 0.0

    print(f"{channel_name} channel:")
    print("  Difference min/max:", diff_array.min(), diff_array.max())
    print("  Shifted min/max:", shifted_diff.min(), shifted_diff.max())
    print("  Encoded output length:", len(encoded_output))
    print("  Dictionary size:", dictionary_size)
    print("  Code length:", code_length)
    print("  Compressed Size:", compressed_size, "bytes")
    print(f"  Entropy: {entropy:.4f} bits/pixel")
    print(f"  Average Code Length: {average_code_length:.4f} bits/code")
    print("  Difference image saved as:", diff_image_path)
    print("  Compressed file saved as:", output_bin_path)

    return compressed_size, entropy, average_code_length


def decompress_difference_channel(input_bin_path):
    with open(input_bin_path, 'rb') as f:
        compressed_data = f.read()

    bit_string = ''.join(format(byte, '08b') for byte in compressed_data)
    bit_string = remove_padding(bit_string)

    width, height, code_length, encoded_bits = extract_metadata(bit_string)
    encoded_values = binary_string_to_int_list(encoded_bits, code_length)
    decoded_shifted_list = lzw_decode_difference(encoded_values)

    expected_pixels = height * width
    if len(decoded_shifted_list) != expected_pixels:
        raise ValueError(
            f"Decoded pixel count does not match expected channel size. "
            f"Expected {expected_pixels}, got {len(decoded_shifted_list)}"
        )

    decoded_shifted_array = reshape_channel(decoded_shifted_list, (height, width))
    decoded_diff_array = unshift_difference_values(decoded_shifted_array)

    restored_channel = reconstruct_from_difference(decoded_diff_array)
    restored_channel = np.clip(restored_channel, 0, 255).astype(np.uint8)

    return restored_channel


if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.realpath(__file__))

    input_path = os.path.join(current_directory, "thumbs_up.bmp")

    red_img_path = os.path.join(current_directory, "thumbs_up_red.bmp")
    green_img_path = os.path.join(current_directory, "thumbs_up_green.bmp")
    blue_img_path = os.path.join(current_directory, "thumbs_up_blue.bmp")

    red_diff_path = os.path.join(current_directory, "thumbs_up_red_difference.bmp")
    green_diff_path = os.path.join(current_directory, "thumbs_up_green_difference.bmp")
    blue_diff_path = os.path.join(current_directory, "thumbs_up_blue_difference.bmp")

    red_bin_path = os.path.join(current_directory, "thumbs_up_red_difference_compressed.bin")
    green_bin_path = os.path.join(current_directory, "thumbs_up_green_difference_compressed.bin")
    blue_bin_path = os.path.join(current_directory, "thumbs_up_blue_difference_compressed.bin")

    restored_path = os.path.join(current_directory, "thumbs_up_restored_color_difference.bmp")

    print("Input path:", input_path)
    print("File exists:", os.path.exists(input_path))

    img = read_image(input_path)
    image_array = pil_to_np(img)

    print("Original image shape:", image_array.shape)

    if len(image_array.shape) != 3 or image_array.shape[2] != 3:
        raise ValueError("Input image is not a color RGB image.")

    red, green, blue = split_rgb_channels(image_array)

    save_channel_image(red, red_img_path)
    save_channel_image(green, green_img_path)
    save_channel_image(blue, blue_img_path)

    red_size, red_entropy, red_avg = compress_difference_channel(
        red, red_bin_path, red_diff_path, "Red"
    )
    green_size, green_entropy, green_avg = compress_difference_channel(
        green, green_bin_path, green_diff_path, "Green"
    )
    blue_size, blue_entropy, blue_avg = compress_difference_channel(
        blue, blue_bin_path, blue_diff_path, "Blue"
    )

    red_restored = decompress_difference_channel(red_bin_path)
    green_restored = decompress_difference_channel(green_bin_path)
    blue_restored = decompress_difference_channel(blue_bin_path)

    restored_color = merge_rgb_channels(red_restored, green_restored, blue_restored)
    np_to_pil(restored_color).save(restored_path)

    original_size = os.path.getsize(input_path)
    total_compressed_size = red_size + green_size + blue_size
    compression_ratio = total_compressed_size / original_size if original_size != 0 else 0

    same = np.array_equal(image_array, restored_color)

    print("\nTotal Results:")
    print("Original Size:", original_size, "bytes")
    print("Total Compressed Size:", total_compressed_size, "bytes")
    print(f"Compression Ratio (CR): {compression_ratio:.4f}")
    print("Red component image saved as:", red_img_path)
    print("Green component image saved as:", green_img_path)
    print("Blue component image saved as:", blue_img_path)
    print("Restored color image saved as:", restored_path)
    print("Original and restored color images are the same:", same)