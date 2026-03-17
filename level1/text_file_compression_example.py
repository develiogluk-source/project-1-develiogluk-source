import os
from LZW import LZWCoding

current_directory = os.path.dirname(os.path.realpath(__file__))
input_path = os.path.join(current_directory, "sample.txt")

lzw = LZWCoding(input_path, "text")
output_path = lzw.compress_text_file()
print("Compressed file path:", output_path)