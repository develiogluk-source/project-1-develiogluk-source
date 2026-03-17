import os
import re
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import numpy as np


class LZWGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LZW Compression GUI")
        self.root.geometry("1280x780")
        self.root.configure(bg="#dfe5ef")

        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        self.project_root = os.path.dirname(self.base_dir)

        self.selected_file = None
        self.current_preview_image = None
        self.left_photo = None
        self.right_photo = None

        self.methods = {
            "Level 1: Compression": {
                "script": os.path.join(self.project_root, "level1", "text_file_compression_example.py"),
                "type": "text",
                "copy_name": "sample.txt",
                "output": os.path.join(self.project_root, "level1", "sample_compressed.bin"),
            },
            "Level 1: Decompression": {
                "script": os.path.join(self.project_root, "level1", "text_file_decompression_example.py"),
                "type": "binary",
                "copy_name": "sample_compressed.bin",
                "output": os.path.join(self.project_root, "level1", "sample_decompressed.txt"),
            },
            "Level 2: Compression": {
                "script": os.path.join(self.project_root, "level2.1.1.1", "basic_image_operations", "image_lzw.py"),
                "type": "image",
                "copy_name": "thumbs_up.bmp",
                "output": os.path.join(self.project_root, "level2.1.1.1", "basic_image_operations", "thumbs_up_lzw_compressed.bin"),
            },
            "Level 2: Decompression": {
                "script": os.path.join(self.project_root, "level2.1.1.1", "basic_image_operations", "image_lzw.py"),
                "type": "binary",
                "copy_name": "thumbs_up_lzw_compressed.bin",
                "output": os.path.join(self.project_root, "level2.1.1.1", "basic_image_operations", "thumbs_up_restored.bmp"),
            },
            "Level 3: Compression": {
                "script": os.path.join(self.project_root, "level3", "image_lzw_level3.py"),
                "type": "image",
                "copy_name": "thumbs_up.bmp",
                "output": os.path.join(self.project_root, "level3", "thumbs_up_difference_lzw_compressed.bin"),
            },
            "Level 3: Decompression": {
                "script": os.path.join(self.project_root, "level3", "image_lzw_level3.py"),
                "type": "image",
                "copy_name": "thumbs_up.bmp",
                "output": os.path.join(self.project_root, "level3", "thumbs_up_difference_restored.bmp"),
            },
            "Level 4: Compression": {
                "script": os.path.join(self.project_root, "level4", "image_lzw_level4.py"),
                "type": "image",
                "copy_name": "thumbs_up.bmp",
                "output": os.path.join(self.project_root, "level4", "thumbs_up_red_compressed.bin"),
            },
            "Level 4: Decompression": {
                "script": os.path.join(self.project_root, "level4", "image_lzw_level4.py"),
                "type": "image",
                "copy_name": "thumbs_up.bmp",
                "output": os.path.join(self.project_root, "level4", "thumbs_up_restored_color.bmp"),
            },
            "Level 5: Compression": {
                "script": os.path.join(self.project_root, "level5", "image_lzw_level5.py"),
                "type": "image",
                "copy_name": "thumbs_up.bmp",
                "output": os.path.join(self.project_root, "level5", "thumbs_up_red_difference_compressed.bin"),
            },
            "Level 5: Decompression": {
                "script": os.path.join(self.project_root, "level5", "image_lzw_level5.py"),
                "type": "image",
                "copy_name": "thumbs_up.bmp",
                "output": os.path.join(self.project_root, "level5", "thumbs_up_restored_color_difference.bmp"),
            },
        }

        self.build_ui()

    def build_ui(self):
        top = tk.Frame(self.root, bg="#eef2f7", height=90)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(
            top,
            text="LZW Compression GUI",
            font=("Arial", 24, "bold"),
            bg="#eef2f7",
            fg="#1f1f1f"
        ).place(x=20, y=15)

        tk.Label(
            top,
            text="Select a file, choose a level, and run compression or decompression.",
            font=("Arial", 10),
            bg="#eef2f7",
            fg="#666666"
        ).place(x=22, y=55)

        tk.Label(top, text="File", font=("Arial", 10, "bold"), bg="#eef2f7").place(x=420, y=12)
        tk.Button(
            top,
            text="Browse",
            width=16,
            command=self.select_file,
            bg="white",
            relief="groove",
            font=("Arial", 10)
        ).place(x=420, y=35)

        tk.Label(top, text="Method", font=("Arial", 10, "bold"), bg="#eef2f7").place(x=620, y=12)
        self.method_var = tk.StringVar()
        self.method_combo = ttk.Combobox(
            top,
            textvariable=self.method_var,
            values=list(self.methods.keys()),
            state="readonly",
            width=28,
            font=("Arial", 10)
        )
        self.method_combo.place(x=620, y=35)
        self.method_combo.current(0)

        tk.Label(top, text="Action", font=("Arial", 10, "bold"), bg="#eef2f7").place(x=860, y=12)
        tk.Button(
            top,
            text="Run",
            width=16,
            command=self.run_method,
            bg="white",
            relief="groove",
            font=("Arial", 10, "bold")
        ).place(x=860, y=35)

        self.file_label = tk.Label(
            self.root,
            text="No file selected",
            bg="#dfe5ef",
            fg="#2e7d32",
            font=("Arial", 11, "bold"),
            anchor="w",
            justify="left",
            wraplength=1180
        )
        self.file_label.place(x=30, y=95)

        main = tk.Frame(self.root, bg="#6887cc")
        main.place(x=20, y=120, width=1240, height=630)

        tk.Label(main, text="Original Input", font=("Arial", 15, "bold"), bg="#6887cc", fg="white").place(x=55, y=20)
        tk.Label(main, text="Output Preview", font=("Arial", 15, "bold"), bg="#6887cc", fg="white").place(x=755, y=20)

        self.left_frame = tk.Frame(main, bg="white", highlightbackground="#b7d36b", highlightthickness=2)
        self.left_frame.place(x=45, y=55, width=380, height=280)
        self.left_frame.pack_propagate(False)

        self.left_label = tk.Label(
            self.left_frame,
            text="Original File",
            bg="white",
            font=("Arial", 16),
            justify="center",
            wraplength=340
        )
        self.left_label.pack(expand=True, fill="both")

        self.right_frame = tk.Frame(main, bg="white", highlightbackground="#b7d36b", highlightthickness=2)
        self.right_frame.place(x=745, y=55, width=380, height=280)
        self.right_frame.pack_propagate(False)

        self.right_label = tk.Label(
            self.right_frame,
            text="Output File",
            bg="white",
            font=("Arial", 16),
            justify="center",
            wraplength=340
        )
        self.right_label.pack(expand=True, fill="both")

        tk.Label(main, text="Preview Modes", font=("Arial", 11, "bold"), bg="#6887cc", fg="white").place(x=45, y=365)

        btn_style = {"width": 14, "bg": "white", "relief": "groove", "font": ("Arial", 10)}
        tk.Button(main, text="Original", command=lambda: self.show_channel("color"), **btn_style).place(x=45, y=390)
        tk.Button(main, text="Grayscale", command=lambda: self.show_channel("gray"), **btn_style).place(x=185, y=390)
        tk.Button(main, text="Red", command=lambda: self.show_channel("red"), **btn_style).place(x=325, y=390)
        tk.Button(main, text="Green", command=lambda: self.show_channel("green"), **btn_style).place(x=465, y=390)
        tk.Button(main, text="Blue", command=lambda: self.show_channel("blue"), **btn_style).place(x=605, y=390)

        tk.Label(
            main,
            text="Metrics",
            font=("Arial", 10, "bold"),
            bg="#6887cc",
            fg="white",
            relief="groove",
            padx=6,
            pady=2
        ).place(x=785, y=310)

        self.metrics = tk.Label(
            main,
            text=(
                "Entropy: -\n\n"
                "Average Code Length: -\n\n"
                "Compression Ratio: -\n\n"
                "Input Size: -\n\n"
                "Compressed Size: -\n\n"
                "Difference: -"
            ),
            bg="#6887cc",
            fg="white",
            font=("Arial", 11, "bold"),
            justify="left",
            anchor="nw"
        )
        self.metrics.place(x=785, y=350)

        tk.Label(main, text="Operation Log", font=("Arial", 11, "bold"), bg="#6887cc", fg="white").place(x=45, y=460)

        self.console = tk.Text(
            main,
            width=85,
            height=8,
            font=("Consolas", 10),
            bg="white",
            fg="black",
            relief="flat",
            wrap="word"
        )
        self.console.place(x=45, y=485, width=700, height=110)

        scrollbar = tk.Scrollbar(main, command=self.console.yview)
        scrollbar.place(x=745, y=485, height=110)
        self.console.config(yscrollcommand=scrollbar.set)

    def select_file(self):
        method = self.method_var.get()

        if "Level 1" in method:
            if "Compression" in method:
                filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
            else:
                filetypes = [("Binary files", "*.bin"), ("All files", "*.*")]
        else:
            if "Decompression" in method and "Level 2" in method:
                filetypes = [("Binary files", "*.bin"), ("All files", "*.*")]
            elif "Decompression" in method:
                filetypes = [("Image files", "*.bmp *.png *.jpg *.jpeg"), ("All files", "*.*")]
            else:
                filetypes = [("Image files", "*.bmp *.png *.jpg *.jpeg"), ("All files", "*.*")]

        path = filedialog.askopenfilename(title="Select file", filetypes=filetypes)
        if not path:
            return

        self.selected_file = path
        self.file_label.config(text=path)

        ext = os.path.splitext(path)[1].lower()
        if ext in [".bmp", ".png", ".jpg", ".jpeg"]:
            with Image.open(path) as im:
                self.current_preview_image = im.convert("RGB").copy()
        else:
            self.current_preview_image = None

        self.preview_file(path, "left")

    def preview_pil(self, img, side):
        img = img.copy()
        img.thumbnail((350, 250))
        tk_img = ImageTk.PhotoImage(img)

        if side == "left":
            self.left_photo = tk_img
            self.left_label.config(image=tk_img, text="")
        else:
            self.right_photo = tk_img
            self.right_label.config(image=tk_img, text="")

    def preview_file(self, path, side):
        label = self.left_label if side == "left" else self.right_label
        ext = os.path.splitext(path)[1].lower()

        if ext in [".bmp", ".png", ".jpg", ".jpeg"]:
            with Image.open(path) as im:
                self.preview_pil(im.convert("RGB"), side)

        elif ext == ".txt":
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(900)
            except Exception:
                content = "Text preview unavailable."

            label.config(
                image="",
                text=content,
                font=("Consolas", 10),
                justify="left",
                anchor="nw",
                wraplength=340,
                padx=10,
                pady=10
            )

        elif ext == ".bin":
            size_ = os.path.getsize(path)
            label.config(
                image="",
                text=(
                    "Compression completed.\n\n"
                    f"{os.path.basename(path)}\n\n"
                    f"Binary file size: {size_} bytes\n\n"
                    "Binary output cannot be displayed as an image."
                ),
                font=("Arial", 13),
                justify="center",
                wraplength=330
            )
        else:
            label.config(image="", text="Unsupported preview", font=("Arial", 12))

    def show_channel(self, mode):
        if self.current_preview_image is None:
            messagebox.showinfo("Info", "Select an image first.")
            return

        arr = np.array(self.current_preview_image)

        if mode == "color":
            img = self.current_preview_image.copy()
        elif mode == "gray":
            img = self.current_preview_image.convert("L").convert("RGB")
        elif mode == "red":
            x = np.zeros_like(arr)
            x[:, :, 0] = arr[:, :, 0]
            img = Image.fromarray(x)
        elif mode == "green":
            x = np.zeros_like(arr)
            x[:, :, 1] = arr[:, :, 1]
            img = Image.fromarray(x)
        elif mode == "blue":
            x = np.zeros_like(arr)
            x[:, :, 2] = arr[:, :, 2]
            img = Image.fromarray(x)
        else:
            return

        self.preview_pil(img, "left")

    def copy_selected_file(self, info):
        if not self.selected_file:
            raise Exception("Please select a file first.")

        script_dir = os.path.dirname(info["script"])
        target = os.path.join(script_dir, info["copy_name"])
        ext = os.path.splitext(self.selected_file)[1].lower()

        if os.path.abspath(self.selected_file) == os.path.abspath(target):
            return

        if info["type"] in ["text", "binary"]:
            shutil.copy2(self.selected_file, target)
        else:
            if ext == ".bmp":
                shutil.copy2(self.selected_file, target)
            else:
                with Image.open(self.selected_file) as im:
                    im.convert("RGB").save(target)

    def run_method(self):
        method = self.method_var.get()
        info = self.methods[method]
        script_path = info["script"]

        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"Script not found:\n{script_path}")
            return

        try:
            self.copy_selected_file(info)

            env = os.environ.copy()
            env["PYTHONPATH"] = self.project_root + os.pathsep + env.get("PYTHONPATH", "")

            if method == "Level 2: Compression":
                cmd = [sys.executable, script_path, "compress"]
            elif method == "Level 2: Decompression":
                cmd = [sys.executable, script_path, "decompress"]
            else:
                cmd = [sys.executable, script_path]

            result = subprocess.run(
                cmd,
                cwd=os.path.dirname(script_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                env=env
            )

            output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()

            self.console.delete("1.0", tk.END)
            self.console.insert(tk.END, output if output else "No console output.")

            if result.returncode != 0:
                messagebox.showerror("Script Error", output or "Unknown error")
                return

            self.update_metrics(output)

            output_path = info["output"]
            if os.path.exists(output_path):
                self.preview_file(output_path, "right")
            else:
                self.right_label.config(image="", text="Output not found", font=("Arial", 14))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_metrics(self, output):
        def pick(*patterns):
            for p in patterns:
                m = re.search(p, output, re.IGNORECASE)
                if m:
                    return m.group(1)
            return "-"

        entropy = pick(
            r"Entropy:\s*([0-9.]+(?:\s*\w+/\w+)?)",
            r"Entropy\s*=\s*([0-9.]+(?:\s*\w+/\w+)?)"
        )

        avg = pick(
            r"Average Code Length:\s*([0-9.]+(?:\s*\w+/\w+)?)",
            r"Code Length:\s*([0-9.]+(?:\s*\w+/\w+)?)",
            r"Average code length\s*:\s*([0-9.]+(?:\s*\w+/\w+)?)"
        )

        cr = pick(
            r"Compression Ratio\s*\(CR\):\s*([0-9.]+)",
            r"Compression Ratio:\s*([0-9.]+)",
            r"Compression ratio\s*:\s*([0-9.]+)",
            r"CR\s*:\s*([0-9.]+)"
        )

        original_size = pick(
            r"Original Size:\s*([0-9.]+\s*[KMG]?B?(?:\s*bytes)?)",
            r"Original data size\s*:\s*([0-9.]+\s*[KMG]?B?(?:\s*bytes)?)",
            r"Original size\s*:\s*([0-9.]+\s*[KMG]?B?(?:\s*bytes)?)",
            r"Input Size:\s*([0-9.]+\s*[KMG]?B?(?:\s*bytes)?)"
        )

        compressed_size = pick(
            r"Compressed Size:\s*([0-9.]+\s*[KMG]?B?(?:\s*bytes)?)",
            r"Compressed file size\s*:\s*([0-9.]+\s*[KMG]?B?(?:\s*bytes)?)",
            r"Total Compressed Size:\s*([0-9.]+\s*[KMG]?B?(?:\s*bytes)?)"
        )

        same = (
            "True" if ("True" in output or "IDENTICAL" in output or "SAME" in output)
            else "False" if ("False" in output or "DIFFERENT" in output)
            else "-"
        )

        self.metrics.config(
            text=(
                f"Entropy: {entropy}\n\n"
                f"Average Code Length: {avg}\n\n"
                f"Compression Ratio: {cr}\n\n"
                f"Input Size: {original_size}\n\n"
                f"Compressed Size: {compressed_size}\n\n"
                f"Difference: {same}"
            )
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = LZWGuiApp(root)
    root.mainloop()