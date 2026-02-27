from PIL import Image, ImageTk   # used Python Imaging Library (PIL) modules
import numpy as np   # a fundamental package for scientific computing
import os   # os module is used for file and directory operations
import tkinter as tk
from tkinter import filedialog, messagebox

# Global değişkenlerin ilklendirilmesi
# -------------------------------------------------------------------------------
current_directory = os.path.dirname(os.path.realpath(__file__))
image_file_path = os.path.join(current_directory, 'thumbs_up.bmp') # Varsayılan dosya yolu

def start():
   gui = tk.Tk() 
   gui.title('Image Operations - Proje Tamamlandı')
   gui['bg'] = 'SeaGreen1'

   frame = tk.Frame(gui)
   frame.grid(row = 0, column = 0, padx = 15, pady = 15)
   frame['bg'] = 'DodgerBlue4'

   # Varsayılan resmi yüklemeye çalış, yoksa boş panel oluştur
   try:
       gui_img = ImageTk.PhotoImage(file = image_file_path)
       gui_img_panel = tk.Label(frame, image = gui_img)
       gui_img_panel.photo_ref = gui_img
   except:
       gui_img_panel = tk.Label(frame, text="Resim Seçiniz", width=50, height=20)
   
   gui_img_panel.grid(row = 0, column = 0, columnspan = 5, padx = 10, pady = 10)

   # Butonlar
   btn1 = tk.Button(frame, text = 'Open Image', width = 12, command=lambda:open_image(gui_img_panel))
   btn1.grid(row = 1, column = 0, pady=10) 

   btn2 = tk.Button(frame, text = 'Grayscale', bg = 'gray', width = 12, command=lambda:display_in_grayscale(gui_img_panel))
   btn2.grid(row = 1, column = 1)

   btn3 = tk.Button(frame, text = 'Red', bg = 'red', width = 12, command=lambda:display_color_channel(gui_img_panel, 'red'))
   btn3.grid(row = 1, column = 2)

   btn4 = tk.Button(frame, text = 'Green', bg = 'SpringGreen2', width = 12, command=lambda:display_color_channel(gui_img_panel, 'green'))
   btn4.grid(row = 1, column = 3)

   btn5 = tk.Button(frame, text = 'Blue', bg = 'DodgerBlue2', width = 12, command=lambda:display_color_channel(gui_img_panel, 'blue'))
   btn5.grid(row = 1, column = 4) 

   gui.mainloop()

def open_image(image_panel):
   global image_file_path
   file_path = filedialog.askopenfilename(initialdir = current_directory, 
                                          title = 'Select an image file', 
                                          filetypes = [('bmp files', '*.bmp')])
   if file_path == '':
      messagebox.showinfo('Warning', 'No image file is selected/opened.')
   else:
      image_file_path = file_path
      img = Image.open(image_file_path)
      tk_img = ImageTk.PhotoImage(img) 
      image_panel.config(image = tk_img) 
      image_panel.photo_ref = tk_img

def display_in_grayscale(image_panel):
   if not os.path.exists(image_file_path):
      messagebox.showerror("Hata", "Önce bir resim açmalısınız!")
      return

   img_rgb = Image.open(image_file_path)
   img_grayscale = img_rgb.convert('L')
   
   # --- DOSYAYI KAYDETME ADIMI ---
   output_name = "thumbs_up_grayscale.bmp"
   img_grayscale.save(output_name)
   print(f"\nİşlem Başarılı: {output_name} kaydedildi.")
   # ------------------------------

   # Terminal Bilgileri
   print('----------------------------------------------------------------------')
   print('Color Dimensions:', pil_to_np(img_rgb).shape)
   print('Grayscale Dimensions:', pil_to_np(img_grayscale).shape)
   
   img = ImageTk.PhotoImage(image = img_grayscale) 
   image_panel.config(image = img) 
   image_panel.photo_ref = img
   messagebox.showinfo("Bilgi", f"Resim griye çevrildi ve '{output_name}' olarak kaydedildi.")

def display_color_channel(image_panel, channel):
   if not os.path.exists(image_file_path): return
   
   channel_dict = {'red': 0, 'green': 1, 'blue': 2}
   channel_index = channel_dict[channel]
   
   img_rgb = Image.open(image_file_path)
   image_array = pil_to_np(img_rgb)
   
   # Verimlilik için NumPy maskeleme (for döngüsü yerine)
   new_array = np.zeros_like(image_array)
   new_array[:, :, channel_index] = image_array[:, :, channel_index]
   
   pil_img = np_to_pil(new_array)
   img = ImageTk.PhotoImage(image = pil_img) 
   image_panel.config(image = img) 
   image_panel.photo_ref = img

def pil_to_np(img):
   return np.array(img)

def np_to_pil(img_array):
   return Image.fromarray(np.uint8(img_array))

if __name__== '__main__':
   start()