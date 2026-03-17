import os
from level1.LZW import LZWCoding

filename = 'sample'
lzw = LZWCoding(filename, 'text')
output_path = lzw.decompress_text_file()

current_directory = os.path.dirname(os.path.realpath(__file__))

original_path = os.path.join(current_directory, filename + '.txt')
decompressed_path = os.path.join(current_directory, filename + '_decompressed.txt')

with open(original_path, 'r', encoding='utf-8') as file1, open(decompressed_path, 'r', encoding='utf-8') as file2:
    original_text = file1.read()
    decompressed_text = file2.read()

if original_text == decompressed_text:
    print(f"{filename}.txt and {filename}_decompressed.txt are the same.")
else:
    print(f"{filename}.txt and {filename}_decompressed.txt are NOT the same.")