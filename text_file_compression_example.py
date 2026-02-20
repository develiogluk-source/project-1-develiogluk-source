from LZW import LZWCoding

# read and compress the file sample.txt
filename = 'sample'   # filename without the extension 
lzw = LZWCoding(filename, 'text')
output_path = lzw.compress_text_file()


# calculate compression statistics
original_size = os.path.getsize(original_path)
compressed_path = current_directory + '/' + filename + '_compressed.bin'
compressed_size = os.path.getsize(compressed_path)

CR = compressed_size / original_size
CF = original_size / compressed_size
SS = (original_size - compressed_size) / original_size

print("Compression Ratio (CR): {:.4f}".format(CR))
print("Compression Factor (CF): {:.4f}".format(CF))
print("Space Saving (SS): {:.4f}".format(SS))