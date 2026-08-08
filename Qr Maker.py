import io
import os
import subprocess
import sys
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import qrcode

try:
    from ctypes import windll

    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

try:
    import win32clipboard
    import win32con

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class QRCodeApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.COLOR_BG = "#121212"
        self.COLOR_CARD = "#1E1E1E"
        self.COLOR_PRIMARY = "#3B82F6"
        self.COLOR_PRIMARY_HOVER = "#2563EB"
        self.COLOR_SUCCESS = "#22C55E"
        self.COLOR_SUCCESS_HOVER = "#16A34A"
        self.COLOR_DANGER = "#EF4444"
        self.COLOR_DANGER_HOVER = "#DC2626"
        self.COLOR_BORDER = "#2A2A2A"
        self.COLOR_TEXT = "#FFFFFF"
        self.COLOR_TEXT_SECONDARY = "#B0B0B0"

        self.title("QR Code Generator")
        self.geometry("460x720")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=self.COLOR_BG)

        self.output_dir = "Generated QR"
        self.current_qr_path = None
        self.current_qr_image = None
        self.animation_step = 0

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self._setup_ui()
        self._bind_shortcuts()

    def _setup_ui(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=24, pady=24)

        self.header_frame = ctk.CTkFrame(
            self.main_container, fg_color="transparent"
        )
        self.header_frame.pack(fill="x", pady=(0, 16))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="QR Code Generator",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.COLOR_TEXT,
        )
        self.title_label.pack()

        self.entry_frame = ctk.CTkFrame(
            self.main_container, fg_color="transparent"
        )
        self.entry_frame.pack(fill="x", pady=(0, 16))

        self.url_entry = ctk.CTkEntry(
            self.entry_frame,
            placeholder_text="Paste your URL here...",
            height=48,
            corner_radius=12,
            border_width=1,
            border_color=self.COLOR_BORDER,
            fg_color=self.COLOR_CARD,
            text_color=self.COLOR_TEXT,
            placeholder_text_color=self.COLOR_TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=14),
        )
        self.url_entry.pack(fill="x")
        self.url_entry.bind("<Button-3>", self._show_context_menu)

        self.generate_btn = ctk.CTkButton(
            self.main_container,
            text="Generate QR Code",
            height=48,
            corner_radius=12,
            fg_color=self.COLOR_PRIMARY,
            hover_color=self.COLOR_PRIMARY_HOVER,
            text_color=self.COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            command=self.generate_qr,
        )
        self.generate_btn.pack(fill="x", pady=(0, 16))

        self.preview_card = ctk.CTkFrame(
            self.main_container,
            corner_radius=16,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER,
        )
        self.preview_card.pack(fill="both", expand=True, pady=(0, 16))

        self.qr_label = ctk.CTkLabel(
            self.preview_card,
            text="Your QR Code will appear here",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.COLOR_TEXT_SECONDARY,
        )
        self.qr_label.pack(expand=True, fill="both", padx=16, pady=16)

        self.status_banner = ctk.CTkFrame(
            self.main_container,
            height=36,
            corner_radius=8,
            fg_color="transparent",
        )
        self.status_banner.pack(fill="x", pady=(0, 12))

        self.status_label = ctk.CTkLabel(
            self.status_banner,
            text="Ready",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.COLOR_TEXT_SECONDARY,
        )
        self.status_label.pack(expand=True)

        self.actions_frame = ctk.CTkFrame(
            self.main_container, fg_color="transparent"
        )
        self.actions_frame.columnconfigure((0, 1), weight=1, uniform="btn")

        self.btn_open = ctk.CTkButton(
            self.actions_frame,
            text="Open Folder",
            height=38,
            corner_radius=10,
            fg_color=self.COLOR_CARD,
            hover_color=self.COLOR_BORDER,
            text_color=self.COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.open_folder,
        )
        self.btn_open.grid(row=0, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.btn_save_as = ctk.CTkButton(
            self.actions_frame,
            text="Save As",
            height=38,
            corner_radius=10,
            fg_color=self.COLOR_CARD,
            hover_color=self.COLOR_BORDER,
            text_color=self.COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.save_as,
        )
        self.btn_save_as.grid(row=0, column=1, padx=(4, 0), pady=4, sticky="ew")

        self.btn_copy = ctk.CTkButton(
            self.actions_frame,
            text="Copy Image",
            height=38,
            corner_radius=10,
            fg_color=self.COLOR_CARD,
            hover_color=self.COLOR_BORDER,
            text_color=self.COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.copy_image,
        )
        self.btn_copy.grid(row=1, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.btn_clear = ctk.CTkButton(
            self.actions_frame,
            text="Clear",
            height=38,
            corner_radius=10,
            fg_color=self.COLOR_DANGER,
            hover_color=self.COLOR_DANGER_HOVER,
            text_color=self.COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.clear_all,
        )
        self.btn_clear.grid(row=1, column=1, padx=(4, 0), pady=4, sticky="ew")

        # Context Menu 
        self.context_menu = tk.Menu(
            self,
            tearoff=0,
            bg=self.COLOR_CARD,
            fg=self.COLOR_TEXT,
            activebackground=self.COLOR_PRIMARY,
            activeforeground=self.COLOR_TEXT,
            bd=1,
            relief="flat",
        )
        self.context_menu.add_command(
            label="Cut", command=lambda: self._trigger_shortcut(88)
        )
        self.context_menu.add_command(
            label="Copy", command=lambda: self._trigger_shortcut(67)
        )
        self.context_menu.add_command(
            label="Paste", command=lambda: self._trigger_shortcut(86)
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Select All", command=lambda: self._trigger_shortcut(65)
        )

    def _bind_shortcuts(self):
        self.url_entry.bind("<Control-KeyPress>", self._handle_keyboard_shortcuts)
        self.bind("<Return>", lambda e: self.generate_qr())

    def _handle_keyboard_shortcuts(self, event):
        if event.keycode == 65:
            self.url_entry.select_range(0, tk.END)
            self.url_entry.icursor(tk.END)
            return "break"
        elif event.keycode == 86:
            try:
                self.url_entry.insert(tk.INSERT, self.clipboard_get())
            except tk.TclError:
                pass
            return "break"
        elif event.keycode == 67:
            try:
                self.clipboard_clear()
                self.clipboard_append(self.url_entry.selection_get())
            except tk.TclError:
                pass
            return "break"
        elif event.keycode == 88:
            try:
                self.clipboard_clear()
                self.clipboard_append(self.url_entry.selection_get())
                self.url_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            return "break"

    def _trigger_shortcut(self, keycode):
        class DummyEvent:

            def __init__(self, kc):
                self.keycode = kc

        self._handle_keyboard_shortcuts(DummyEvent(keycode))

    def _show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _show_status(self, message, is_error=False, is_success=False):
        if is_error:
            fg_col = "#3A1C1C"
            txt_col = self.COLOR_DANGER
        elif is_success:
            fg_col = "#1C3A27"
            txt_col = self.COLOR_SUCCESS
        else:
            fg_col = "transparent"
            txt_col = self.COLOR_TEXT_SECONDARY

        self.status_banner.configure(fg_color=fg_col)
        self.status_label.configure(text=message, text_color=txt_col)

    def _get_next_filename(self):
        i = 1
        while os.path.exists(os.path.join(self.output_dir, f"qrcode{i}.png")):
            i += 1
        return f"qrcode{i}.png"

    def generate_qr(self):
        url = self.url_entry.get().strip()

        if not url:
            self._show_status("Please enter a valid URL or text first", is_error=True)
            return

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)

            self.current_qr_image = qr.make_image(
                fill_color="black", back_color="white"
            ).convert("RGB")

            filename = self._get_next_filename()
            self.current_qr_path = os.path.join(self.output_dir, filename)
            self.current_qr_image.save(self.current_qr_path)

            self._animate_qr_render()

            self.actions_frame.pack(fill="x", pady=(4, 0))
            self._show_status(
                f"QR Generated Successfully: {filename}", is_success=True
            )

        except Exception as e:
            self._show_status(f"Error generating QR: {str(e)}", is_error=True)

    def _animate_qr_render(self):
        self.animation_step = 20

        def step():
            if self.animation_step <= 220:
                resized = self.current_qr_image.resize(
                    (self.animation_step, self.animation_step),
                    Image.Resampling.LANCZOS,
                )
                ctk_img = ctk.CTkImage(
                    light_image=resized,
                    dark_image=resized,
                    size=(self.animation_step, self.animation_step),
                )
                self.qr_label.configure(image=ctk_img, text="")
                self.animation_step += 25
                self.after(10, step)

        step()

    def open_folder(self):
        if not self.current_qr_path or not os.path.exists(self.current_qr_path):
            self._show_status("File path not found", is_error=True)
            return

        abs_path = os.path.abspath(self.current_qr_path)
        if sys.platform == "win32":
            subprocess.run(f'explorer /select,"{abs_path}"')
        elif sys.platform == "darwin":
            subprocess.run(["open", "-R", abs_path])
        else:
            subprocess.run(["xdg-open", os.path.dirname(abs_path)])

    def save_as(self):
        if not self.current_qr_image:
            return

        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")],
            initialfile=os.path.basename(self.current_qr_path or "qrcode.png"),
        )
        if file_path:
            self.current_qr_image.save(file_path)
            self._show_status(
                f"Saved as: {os.path.basename(file_path)}", is_success=True
            )

    def copy_image(self):
        if not self.current_qr_image:
            return

        if WIN32_AVAILABLE and sys.platform == "win32":
            output = io.BytesIO()
            self.current_qr_image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            self._show_status("Image copied to clipboard!", is_success=True)
        else:
            self._show_status(
                "Copying images requires 'pywin32' on Windows", is_error=True
            )

    def clear_all(self):
        self.url_entry.delete(0, tk.END)
        self.qr_label.configure(image=None, text="Your QR Code will appear here")
        self.actions_frame.pack_forget()
        self.current_qr_path = None
        self.current_qr_image = None
        self._show_status("Ready")


if __name__ == "__main__":
    app = QRCodeApp()
    app.mainloop()
