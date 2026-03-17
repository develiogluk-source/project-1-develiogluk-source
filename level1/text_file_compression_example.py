from level1.LZW import LZWCoding

filename = 'sample'
lzw = LZWCoding(filename, 'text')
output_path = lzw.compress_text_file()
print("Compressed file path:", output_path)