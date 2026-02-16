from LZW import LZWCoding

# read and compress the file sample.txt
filename = 'sample'   # filename without the extension 
lzw = LZWCoding(filename, 'text')
output_path = lzw.compress_text_file()
