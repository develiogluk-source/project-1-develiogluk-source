import os
import math
import csv


class LZWCoding:
    def __init__(self, path, data_type):
        self.data_type = data_type
        self.path = os.path.abspath(path)
        self.filename, self.file_extension = os.path.splitext(self.path)
        self.current_directory = os.path.dirname(self.path) or os.getcwd()

        if os.path.exists(self.path):
            self.file_size = os.path.getsize(self.path)
        else:
            self.file_size = 0

        self.compressed_file_size = 0
        self.code_length = 9
        self.compression_ratio = 0.0
        self.compression_factor = 0.0
        self.space_saving = 0.0

    def _lzw_compress(self, data):
        dict_size = 256
        dictionary = {chr(i): i for i in range(dict_size)}

        w = ""
        codes = []
        encode_log = []
        step = 1

        for c in data:
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                if w == "":
                    w = c
                    continue

                output_code = dictionary[w]
                codes.append(output_code)

                encode_log.append({
                    "step": step,
                    "w": w,
                    "k": c,
                    "output_code": output_code,
                    "dict_index": dict_size,
                    "dict_symbol": wc
                })
                step += 1

                dictionary[wc] = dict_size
                dict_size += 1
                w = c

        if w:
            codes.append(dictionary[w])
            encode_log.append({
                "step": step,
                "w": w,
                "k": "EOF",
                "output_code": dictionary[w],
                "dict_index": "-",
                "dict_symbol": "-"
            })

        return codes, encode_log

    def _lzw_decompress(self, codes):
        from io import StringIO

        if not codes:
            return "", []

        dict_size = 256
        dictionary = {i: chr(i) for i in range(dict_size)}

        result = StringIO()
        decode_log = []
        step = 1

        w = chr(codes[0])
        result.write(w)

        for k in codes[1:]:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dict_size:
                entry = w + w[0]
            else:
                raise ValueError(f"Bad compressed code: {k}")

            result.write(entry)

            new_symbol = w + entry[0]
            decode_log.append({
                "step": step,
                "w": w,
                "k": k,
                "output_text": entry,
                "dict_index": dict_size,
                "dict_symbol": new_symbol
            })
            step += 1

            dictionary[dict_size] = new_symbol
            dict_size += 1
            w = entry

        return result.getvalue(), decode_log

    def _calculate_code_length(self, codes):
        if not codes:
            return 9
        max_code = max(codes)
        return max(9, math.ceil(math.log2(max_code + 1)) if max_code > 0 else 9)

    def _int_array_to_binary_string(self, int_array, code_length):
        bitstr = ""
        for num in int_array:
            for n in range(code_length):
                if num & (1 << (code_length - 1 - n)):
                    bitstr += "1"
                else:
                    bitstr += "0"
        return bitstr

    def _pad_encoded_text(self, encoded_text):
        extra_padding = (8 - len(encoded_text) % 8) % 8
        encoded_text += "0" * extra_padding
        padded_info = "{0:08b}".format(extra_padding)
        return padded_info + encoded_text

    def _get_byte_array(self, padded_encoded_text):
        if len(padded_encoded_text) % 8 != 0:
            raise ValueError("Encoded text not padded properly.")
        b = bytearray()
        for i in range(0, len(padded_encoded_text), 8):
            byte = int(padded_encoded_text[i:i + 8], 2)
            b.append(byte)
        return b

    def _remove_padding(self, padded_encoded_text, code_length):
        if len(padded_encoded_text) < 8:
            raise ValueError("Compressed data is too short.")

        padded_info = padded_encoded_text[:8]
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

    def _calculate_metrics(self):
        orig = self.file_size
        comp = self.compressed_file_size
        if orig == 0 or comp == 0:
            return
        self.compression_ratio = comp / orig
        self.compression_factor = orig / comp
        self.space_saving = (orig - comp) / orig

    def _print_metrics(self):
        print(f"Original Size: {self.file_size} bytes")
        print(f"Compressed Size: {self.compressed_file_size} bytes")
        print(f"Code Length: {self.code_length} bits")
        print(f"Compression Ratio: {self.compression_ratio:.4f}")
        print(f"Compression Factor: {self.compression_factor:.4f}")
        print(f"Space Saving: {self.space_saving * 100:.2f}%")

    def _save_encode_log(self, encode_log, log_path):
        fieldnames = ["step", "w", "k", "output_code", "dict_index", "dict_symbol"]
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(encode_log)

    def _save_decode_log(self, decode_log, log_path):
        fieldnames = ["step", "w", "k", "output_text", "dict_index", "dict_symbol"]
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(decode_log)

    def compress_text_file(self):
        base_name = os.path.basename(self.filename)
        output_file = base_name + "_compressed.bin"
        log_file = base_name + "_encode_log.csv"
        output_path = os.path.join(self.current_directory, output_file)
        log_path = os.path.join(self.current_directory, log_file)

        with open(self.path, "r", encoding="utf-8") as f:
            text = f.read()

        if text == "":
            with open(output_path, "wb") as f:
                f.write(bytes([9]))
                f.write(bytes([0]))
            self.file_size = os.path.getsize(self.path)
            self.compressed_file_size = os.path.getsize(output_path)
            self._calculate_metrics()
            self._save_encode_log([], log_path)
            print(f"[LZW Compress] '{os.path.basename(self.path)}' -> '{output_file}'")
            self._print_metrics()
            print(f"Encode log saved: '{log_file}' (0 entries)")
            return output_path

        codes, encode_log = self._lzw_compress(text)
        self.code_length = self._calculate_code_length(codes)
        bitstring = self._int_array_to_binary_string(codes, self.code_length)
        padded = self._pad_encoded_text(bitstring)
        byte_array = self._get_byte_array(padded)

        with open(output_path, "wb") as f:
            f.write(bytes([self.code_length]))
            f.write(byte_array)

        self.file_size = os.path.getsize(self.path)
        self.compressed_file_size = os.path.getsize(output_path)
        self._calculate_metrics()
        self._save_encode_log(encode_log, log_path)

        print(f"[LZW Compress] '{os.path.basename(self.path)}' -> '{output_file}'")
        self._print_metrics()
        print(f"Encode log saved: '{log_file}' ({len(encode_log)} entries)")
        print(f"Compressed file path: {output_path}")

        return output_path

    def decompress_text_file(self):
        base_name = os.path.basename(self.filename)
        input_file = base_name + "_compressed.bin"
        output_file = base_name + "_decompressed.txt"
        log_file = base_name + "_decode_log.csv"
        input_path = os.path.join(self.current_directory, input_file)
        output_path = os.path.join(self.current_directory, output_file)
        log_path = os.path.join(self.current_directory, log_file)

        with open(input_path, "rb") as f:
            first_byte = f.read(1)
            if not first_byte:
                raise ValueError("Compressed file is empty.")
            self.code_length = first_byte[0]
            raw_bytes = f.read()

        bitstring = ""
        for byte in raw_bytes:
            bitstring += "{0:08b}".format(byte)

        if bitstring == "":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("")
            self.file_size = os.path.getsize(output_path)
            self.compressed_file_size = os.path.getsize(input_path)
            self._calculate_metrics()
            self._save_decode_log([], log_path)
            print(f"[LZW Decompress] '{input_file}' -> '{output_file}'")
            self._print_metrics()
            print(f"Decode log saved: '{log_file}' (0 entries)")
            return output_path

        codes = self._remove_padding(bitstring, self.code_length)
        text, decode_log = self._lzw_decompress(codes)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        self.file_size = os.path.getsize(output_path)
        self.compressed_file_size = os.path.getsize(input_path)
        self._calculate_metrics()
        self._save_decode_log(decode_log, log_path)

        print(f"[LZW Decompress] '{input_file}' -> '{output_file}'")
        self._print_metrics()
        print(f"Decode log saved: '{log_file}' ({len(decode_log)} entries)")
        print(f"Decompressed file path: {output_path}")

        return output_path