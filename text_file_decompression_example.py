import os  # the os module is used for file and directory operations
from LZW import LZWCoding

# read and decompress the file sample.bin
filename = 'sample'
lzw = LZWCoding(filename, 'text')
output_path = lzw.decompress_text_file()


lz.compress_text_file()

# compare the decompressed file with the original file
# ------------------------------------------------------------------------------
# get the current directory where this program is placed
current_directory = os.path.dirname(os.path.realpath(__file__))
# build the path of the original file
original_file = filename + '.txt'
original_path = current_directory + '/' + original_file
# build the path of the decompressed file
decompressed_file = filename + '_decompressed.txt'
decompressed_path = current_directory + '/' + decompressed_file
# read the contents of both files
with open(original_path, 'r') as file1, open(decompressed_path, 'r') as file2:
   original_text = file1.read()
   decompressed_text = file2.read()
# compare the file contents and print the result
if original_text == decompressed_text:
   print(original_file + ' and ' + decompressed_file + ' are the same.')
else:
   print(original_file + ' and ' + decompressed_file + ' are NOT the same.')
