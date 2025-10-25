import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import qrcode
import io

class QrCodeTab:
    def __init__(self, tab_control, app_config, image_operation):
        self.tab_control = tab_control
        self.app_config = app_config
        self.image_operation = image_operation
        self.frame = ttk.Frame(tab_control)
        self.qr_image = None
        self.qr_image_tk = None
        self.create_widgets()

    def create_widgets(self):
        # Input for QR code data
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(pady=10)

        ttk.Label(input_frame, text="QR Code Data:").pack(side=tk.LEFT, padx=5)
        self.qr_data_entry = ttk.Entry(input_frame, width=50)
        self.qr_data_entry.pack(side=tk.LEFT, padx=5)
        self.qr_data_entry.bind("<KeyRelease>", self.generate_qr_code)

        # QR Code display
        self.qr_canvas = tk.Canvas(self.frame, width=200, height=200, bg="white")
        self.qr_canvas.pack(pady=10)

        # Buttons for adding/deleting from canvas
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=5)

        add_button = ttk.Button(button_frame, text="Add to Canvas", command=self.add_qr_to_canvas)
        add_button.pack(side=tk.LEFT, padx=5)

        delete_button = ttk.Button(button_frame, text="Delete from Canvas", command=self.delete_qr_from_canvas)
        delete_button.pack(side=tk.LEFT, padx=5)

    def generate_qr_code(self, event=None):
        data = self.qr_data_entry.get()
        if data:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

            # Manually make white pixels transparent
            datas = img.getdata()
            new_datas = []
            for item in datas:
                if item[0] == 255 and item[1] == 255 and item[2] == 255:
                    new_datas.append((255, 255, 255, 0)) # Transparent white
                else:
                    new_datas.append(item)
            img.putdata(new_datas)

            self.qr_image = img.resize((200, 200), Image.LANCZOS)

            # Convert PIL Image to PhotoImage for Tkinter
            self.qr_image_tk = ImageTk.PhotoImage(self.qr_image)

            # Display the image on the canvas
            self.qr_canvas.delete("all")
            self.qr_canvas.create_image(0, 0, anchor=tk.NW, image=self.qr_image_tk)
        else:
            self.qr_canvas.delete("all")
            self.qr_image = None
            self.qr_image_tk = None

    def get_qr_code_image(self):
        return self.qr_image

    def add_qr_to_canvas(self):
        if self.qr_image:
            self.image_operation.add_image_to_canvas(self.qr_image)
        else:
            tk.messagebox.showinfo("QR Code", "No QR Code generated yet to add.")

    def delete_qr_from_canvas(self):
        # This assumes the QR code image is selected on the canvas
        # A more robust solution would involve tracking the QR code image's canvas ID
        self.image_operation.delete_selected_image()
