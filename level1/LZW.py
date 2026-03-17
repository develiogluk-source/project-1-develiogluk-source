import os
import math
import csv


class LZWCoding:

    def __init__(self, path, data_type):
        """
        Parameters:
            path      (str): File path WITH extension (e.g. 'sample.txt')
            data_type (str): 'text' or 'image'
        """
        self.path           = path
        self.data_type      = data_type
        self.filename, self.file_extension = os.path.splitext(self.path)
        self.current_directory = os.path.dirname(os.path.realpath(self.path)) or os.getcwd()
        self.file_size            = os.path.getsize(self.path)
        self.compressed_file_size = 0
        self.code_length          = 9      # starts at 9 bits (covers 0-511)
        self.compression_ratio    = 0.0
        self.compression_factor   = 0.0
        self.space_saving         = 0.0

    # ──────────────────────────────────────────────────────────────────
    # CORE LZW ALGORITHM
    # ──────────────────────────────────────────────────────────────────

    def _lzw_compress(self, data):
        """
        LZW compression.
        Returns:
            codes     (list[int])  : output integer codes
            encode_log(list[dict]) : one row per dictionary-add event
        """
        dict_size  = 256
        dictionary = {chr(i): i for i in range(dict_size)}

        w          = ""
        codes      = []
        encode_log = []
        step       = 1

        for c in data:
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                output_code = dictionary[w]
                codes.append(output_code)

                encode_log.append({
                    "step"        : step,
                    "w"           : w,
                    "k"           : c,
                    "output_code" : output_code,
                    "dict_index"  : dict_size,
                    "dict_symbol" : wc
                })
                step += 1

                dictionary[wc] = dict_size
                dict_size      += 1
                w               = c

        # flush last w
        if w:
            codes.append(dictionary[w])
            encode_log.append({
                "step"        : step,
                "w"           : w,
                "k"           : "EOF",
                "output_code" : dictionary[w],
                "dict_index"  : "-",
                "dict_symbol" : "-"
            })

        return codes, encode_log

    def _lzw_decompress(self, codes):
        """
        LZW decompression.
        Returns:
            text       (str)       : reconstructed original text
            decode_log (list[dict]): one row per dictionary-add event
        """
        from io import StringIO

        dict_size  = 256
        dictionary = {i: chr(i) for i in range(dict_size)}

        result     = StringIO()
        decode_log = []
        step       = 1

        w = chr(codes[0])
        result.write(w)

        for k in codes[1:]:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dict_size:
                entry = w + w[0]          # edge case
            else:
                raise ValueError(f"Bad compressed code: {k}")

            result.write(entry)

            new_symbol = w + entry[0]
            decode_log.append({
                "step"        : step,
                "w"           : w,
                "k"           : k,
                "output_text" : entry,
                "dict_index"  : dict_size,
                "dict_symbol" : new_symbol
            })
            step += 1

            dictionary[dict_size] = new_symbol
            dict_size += 1
            w          = entry

        return result.getvalue(), decode_log

    # ──────────────────────────────────────────────────────────────────
    # BIT PACKING  (slide 35, 41-43)
    # ──────────────────────────────────────────────────────────────────

    def _calculate_code_length(self, codes):
        """
        Determine the minimum bit-length needed to represent all codes.
        Minimum is 9 bits (to go above 255 ASCII).
        """
        if not codes:
            return 9
        max_code = max(codes)
        bits     = max(9, math.ceil(math.log2(max_code + 1)) if max_code > 0 else 9)
        return bits

    def _int_array_to_binary_string(self, int_array, code_length):
        """
        Convert each integer in int_array to a fixed-width binary string
        of code_length bits, then concatenate.  (slide 41)
        """
        bitstr = ""
        for num in int_array:
            for n in range(code_length):
                if num & (1 << (code_length - 1 - n)):
                    bitstr += "1"
                else:
                    bitstr += "0"
        return bitstr

    def _pad_encoded_text(self, encoded_text):
        """
        If bit-string length is not a multiple of 8, pad with zeros.
        Prepend 8 bits that store how many zeros were added.  (slide 42)
        """
        extra_padding = 8 - len(encoded_text) % 8
        if extra_padding == 8:
            extra_padding = 0
        encoded_text  += "0" * extra_padding
        padded_info    = "{0:08b}".format(extra_padding)
        return padded_info + encoded_text

    def _get_byte_array(self, padded_encoded_text):
        """
        Split padded bit-string into 8-bit chunks and convert to bytearray.
        (slide 42)
        """
        if len(padded_encoded_text) % 8 != 0:
            raise ValueError("Encoded text not padded properly.")
        b = bytearray()
        for i in range(0, len(padded_encoded_text), 8):
            byte = int(padded_encoded_text[i:i + 8], 2)
            b.append(byte)
        return b

    def _remove_padding(self, padded_encoded_text, code_length):
        """
        Read the first 8 bits to find padding count, strip padding,
        then split remaining bits into code_length-wide integers.  (slide 43)
        """
        padded_info   = padded_encoded_text[:8]
        extra_padding = int(padded_info, 2)
        padded_encoded_text = padded_encoded_text[8:]
        if extra_padding:
            encoded_text = padded_encoded_text[:-extra_padding]
        else:
            encoded_text = padded_encoded_text

        int_codes = []
        for bits in range(0, len(encoded_text), code_length):
            chunk = encoded_text[bits: bits + code_length]
            if len(chunk) == code_length:
                int_codes.append(int(chunk, 2))
        return int_codes

    # ──────────────────────────────────────────────────────────────────
    # METRICS  (slide 36)
    # ──────────────────────────────────────────────────────────────────

    def _calculate_metrics(self):
        """
        CR  = compressed / original
        CF  = original   / compressed
        SS  = (original - compressed) / original
        """
        orig = self.file_size
        comp = self.compressed_file_size
        if orig == 0 or comp == 0:
            return
        self.compression_ratio  = comp / orig
        self.compression_factor = orig / comp
        self.space_saving       = (orig - comp) / orig

    def _print_metrics(self):
        print(f"  Original size      : {self.file_size:,} bytes")
        print(f"  Compressed size    : {self.compressed_file_size:,} bytes")
        print(f"  Code length        : {self.code_length} bits")
        print(f"  Compression Ratio  : {self.compression_ratio:.4f}")
        print(f"  Compression Factor : {self.compression_factor:.4f}")
        print(f"  Space Saving       : {self.space_saving * 100:.2f}%")

    # ──────────────────────────────────────────────────────────────────
    # CSV LOGGING
    # ──────────────────────────────────────────────────────────────────

    def _save_encode_log(self, encode_log, log_path):
        """Save encode log as CSV (mirrors LZW compression table in slide 22)."""
        fieldnames = ["step", "w", "k", "output_code", "dict_index", "dict_symbol"]
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(encode_log)

    def _save_decode_log(self, decode_log, log_path):
        """Save decode log as CSV (mirrors LZW decompression table in slide 24)."""
        fieldnames = ["step", "w", "k", "output_text", "dict_index", "dict_symbol"]
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(decode_log)

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 1 – TEXT COMPRESSION
    # ──────────────────────────────────────────────────────────────────

    def compress_text_file(self):
        """
        Read .txt → LZW encode → bit-pack → save _compressed.bin
        Also saves _encode_log.csv

        Returns:
            str: path of the compressed .bin file
        """
        base_name   = os.path.basename(self.filename)
        output_file = base_name + "_compressed.bin"
        log_file    = base_name + "_encode_log.csv"
        output_path = os.path.join(self.current_directory, output_file)
        log_path    = os.path.join(self.current_directory, log_file)

        # 1. read text
        with open(self.path, "r", encoding="utf-8") as f:
            text = f.read()

        # 2. LZW compress → integer codes + log
        codes, encode_log = self._lzw_compress(text)

        # 3. determine code length
        self.code_length = self._calculate_code_length(codes)

        # 4. integer array → bit string  (slide 41)
        bitstring = self._int_array_to_binary_string(codes, self.code_length)

        # 5. pad bit string  (slide 42)
        padded = self._pad_encoded_text(bitstring)

        # 6. bit string → byte array  (slide 42)
        byte_array = self._get_byte_array(padded)

        # 7. write binary file
        #    byte 0        : code_length so the decoder knows how wide each code is
        #    bytes 1..end  : packed bit data
        with open(output_path, "wb") as f:
            f.write(bytes([self.code_length]))
            f.write(byte_array)

        # 8. update sizes & metrics
        self.compressed_file_size = os.path.getsize(output_path)
        self._calculate_metrics()

        # 9. save encode log CSV
        self._save_encode_log(encode_log, log_path)

        print(f"[LZW Compress] '{os.path.basename(self.path)}'  →  '{output_file}'")
        self._print_metrics()
        print(f"  Encode log saved   : '{log_file}'  ({len(encode_log)} entries)")

        return output_path

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 1 – TEXT DECOMPRESSION
    # ──────────────────────────────────────────────────────────────────

    def decompress_text_file(self):
        """
        Read _compressed.bin → unpack bits → LZW decode → save _decompressed.txt
        Also saves _decode_log.csv

        Returns:
            str: path of the decompressed .txt file
        """
        base_name   = os.path.basename(self.filename)
        input_file  = base_name + "_compressed.bin"
        output_file = base_name + "_decompressed.txt"
        log_file    = base_name + "_decode_log.csv"
        input_path  = os.path.join(self.current_directory, input_file)
        output_path = os.path.join(self.current_directory, output_file)
        log_path    = os.path.join(self.current_directory, log_file)

        # 1. read binary file
        with open(input_path, "rb") as f:
            self.code_length = f.read(1)[0]   # first byte = code_length
            raw_bytes        = f.read()

        # 2. bytes → bit string
        bitstring = ""
        for byte in raw_bytes:
            bitstring += "{0:08b}".format(byte)

        # 3. remove padding → integer codes  (slide 43)
        codes = self._remove_padding(bitstring, self.code_length)

        # 4. LZW decompress → text + log
        text, decode_log = self._lzw_decompress(codes)

        # 5. save decompressed text
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        # 6. metrics  (original file size = decompressed file size)
        self.file_size            = os.path.getsize(output_path)
        self.compressed_file_size = os.path.getsize(input_path)
        self._calculate_metrics()

        # 7. save decode log CSV
        self._save_decode_log(decode_log, log_path)

        print(f"[LZW Decompress] '{input_file}'  →  '{output_file}'")
        self._print_metrics()
        print(f"  Decode log saved   : '{log_file}'  ({len(decode_log)} entries)")

        return output_path