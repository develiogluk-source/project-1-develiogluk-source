import os  # the os module is used for file and directory operations
import math  # the math module provides access to mathematical functions
import csv 
# A class that implements the LZW compression and decompression algorithms as
# well as the necessary utility methods for text files.
# ------------------------------------------------------------------------------
class LZWCoding:
   # A constructor with two input parameters
   # ---------------------------------------------------------------------------
   def __init__(self, filename, data_type):
      self.filename = filename
      self.data_type = data_type
      self.codelength = None

   # ---------------------------------------------------------------------------
   def compress_text_file(self):

      current_directory = os.path.dirname(os.path.realpath(__file__))
      input_file = self.filename + '.txt'
      input_path = current_directory + '/' + input_file

      output_file = self.filename + '_compressed.bin'
      output_path = current_directory + '/' + output_file

      in_file = open(input_path, 'r')
      text = in_file.read()
      in_file.close()

      encoded_text_as_integers = self.encode(text)
      encoded_text = self.int_list_to_binary_string(encoded_text_as_integers)
      encoded_text = self.add_code_length_info(encoded_text)
      padded_encoded_text = self.pad_encoded_data(encoded_text)
      byte_array = self.get_byte_array(padded_encoded_text)

      out_file = open(output_path, 'wb')
      out_file.write(bytes(byte_array))
      out_file.close()

      print(input_file + ' is compressed into ' + output_file + '.')
      print('Original Size: ' + str(len(text)) + ' bytes')
      print('Code Length: ' + str(self.codelength))
      print('Compressed Size: ' + str(len(byte_array)) + ' bytes')

      return output_path

   # ---------------------------------------------------------------------------
   def encode(self, uncompressed_data):

      dict_size = 256
      dictionary = {chr(i): i for i in range(dict_size)}

      w = ''
      result = []

      print("\nw\tk\toutput\tindex\tsymbol")
      print("-" * 50)

      for k in uncompressed_data:
         wk = w + k

         if wk in dictionary:
            w = wk
         else:
            print(w, "\t", k, "\t", dictionary[w], "\t", dict_size, "\t", wk)
            result.append(dictionary[w])
            dictionary[wk] = dict_size
            dict_size += 1
            w = k

      if w:
         print(w, "\t-\t", dictionary[w])
         result.append(dictionary[w])

      self.codelength = math.ceil(math.log2(len(dictionary)))

      print("\nEncoded Output:", result)
      return result

   # ---------------------------------------------------------------------------
   def int_list_to_binary_string(self, int_list):
      bits = []
      for num in int_list:
         for n in range(self.codelength):
            if num & (1 << (self.codelength - 1 - n)):
               bits.append('1')
            else:
               bits.append('0')
      return ''.join(bits)

   # ---------------------------------------------------------------------------
   def add_code_length_info(self, bitstring):
      codelength_info = '{0:08b}'.format(self.codelength)
      return codelength_info + bitstring

   # ---------------------------------------------------------------------------
   def pad_encoded_data(self, encoded_data):
      if len(encoded_data) % 8 != 0:
         extra_bits = 8 - len(encoded_data) % 8
         for i in range(extra_bits):
            encoded_data += '0'
      else:
         extra_bits = 0

      padding_info = '{0:08b}'.format(extra_bits)
      return padding_info + encoded_data

   # ---------------------------------------------------------------------------
   def get_byte_array(self, padded_encoded_data):
      if (len(padded_encoded_data) % 8 != 0):
         print('The compressed data is not padded properly!')
         exit(0)

      b = bytearray()
      for i in range(0, len(padded_encoded_data), 8):
         byte = padded_encoded_data[i: i + 8]
         b.append(int(byte, 2))

      return b

   # ---------------------------------------------------------------------------
   def decompress_text_file(self):

      current_directory = os.path.dirname(os.path.realpath(__file__))
      input_file = self.filename + '_compressed.bin'
      input_path = current_directory + '/' + input_file

      output_file = self.filename + '_decompressed.txt'
      output_path = current_directory + '/' + output_file

      in_file = open(input_path, 'rb')
      compressed_data = in_file.read()
      in_file.close()

      from io import StringIO
      bit_string = StringIO()

      for byte in compressed_data:
         bits = bin(byte)[2:].rjust(8, '0')
         bit_string.write(bits)

      bit_string = bit_string.getvalue()

      bit_string = self.remove_padding(bit_string)
      bit_string = self.extract_code_length_info(bit_string)
      encoded_text = self.binary_string_to_int_list(bit_string)
      decompressed_text = self.decode(encoded_text)

      out_file = open(output_path, 'w')
      out_file.write(decompressed_text)
      out_file.close()

      print(input_file + ' is decompressed into ' + output_file + '.')
      return output_path

   # ---------------------------------------------------------------------------
   def remove_padding(self, padded_encoded_data):
      padding_info = padded_encoded_data[:8]
      encoded_data = padded_encoded_data[8:]
      extra_padding = int(padding_info, 2)

      if extra_padding != 0:
         encoded_data = encoded_data[:-1 * extra_padding]

      return encoded_data

   # ---------------------------------------------------------------------------
   def extract_code_length_info(self, bitstring):
      codelength_info = bitstring[:8]
      self.codelength = int(codelength_info, 2)
      return bitstring[8:]

   # ---------------------------------------------------------------------------
   def binary_string_to_int_list(self, bitstring):
      int_codes = []
      for bits in range(0, len(bitstring), self.codelength):
         int_code = int(bitstring[bits: bits + self.codelength], 2)
         int_codes.append(int_code)
      return int_codes

   # ---------------------------------------------------------------------------
   def encode(self, uncompressed_data):

    import csv

    dict_size = 256
    dictionary = {chr(i): i for i in range(dict_size)}

    w = ''
    result = []

    csv_filename = self.filename + "_encode_log.csv"
    csv_file = open(csv_filename, mode='w', newline='')
    csv_writer = csv.writer(csv_file)

    csv_writer.writerow(["w", "k", "output", "index", "symbol"])

    for k in uncompressed_data:

        wk = w + k

        if wk in dictionary:
            w = wk
        else:

            output_code = dictionary[w]

            # 256'dan küçükse karakter göster
            if output_code < 256:
                output_display = chr(output_code)
            else:
                output_display = output_code

            csv_writer.writerow([
                w,
                k,
                output_display,
                dict_size,
                wk
            ])

            result.append(output_code)

            dictionary[wk] = dict_size
            dict_size += 1

            w = k

    if w:
        output_code = dictionary[w]

        if output_code < 256:
            output_display = chr(output_code)
        else:
            output_display = output_code

        result.append(output_code)

        csv_writer.writerow([
            w,
            "-",
            output_display,
            "-",
            "-"
        ])

    csv_file.close()

    self.codelength = math.ceil(math.log2(len(dictionary)))

    return result