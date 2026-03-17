import os
from LZW import LZWCoding

current_directory = os.path.dirname(os.path.realpath(__file__))
input_path = os.path.join(current_directory, "sample.txt")

lzw = LZWCoding(input_path, "text")
output_path = lzw.decompress_text_file()

original_path = os.path.join(current_directory, "sample.txt")
decompressed_path = os.path.join(current_directory, "sample_decompressed.txt")

with open(original_path, "r", encoding="utf-8") as file1, open(decompressed_path, "r", encoding="utf-8") as file2:
    original_text = file1.read()
    decompressed_text = file2.read()

if original_text == decompressed_text:
    print("sample.txt and sample_decompressed.txt are the same.")
else:
    print("sample.txt and sample_decompressed.txt are NOT the same.")