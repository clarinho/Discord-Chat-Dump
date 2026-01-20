import io
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from PIL import Image, ImageTk
except Exception:  # Pillow not installed
    Image = None
    ImageTk = None


def _download_bytes(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


class ImageViewer(tk.Toplevel):
    """
    Simple image previewer with:
    - Fit-to-window resizing
    - Fullscreen toggle button
    - ESC to exit fullscreen
    """
    def __init__(self, parent: tk.Tk, title: str, url: str):
        super().__init__(parent)
        self.parent = parent
        self.url = url
        self.title(title or "Image Preview")
        self.geometry("900x650")
        self.minsize(500, 400)

        self._is_fullscreen = False
        self._pil_image = None
        self._photo = None

        self._build_ui()
        self.bind("<Configure>", lambda e: self._render_fit())
        self.bind("<Escape>", lambda e: self._exit_fullscreen())

        self._load_image()

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)

        self.btn_fullscreen = ttk.Button(top, text="Fullscreen", command=self._toggle_fullscreen)
        self.btn_fullscreen.pack(side=tk.LEFT)

        self.btn_close = ttk.Button(top, text="Close", command=self.destroy)
        self.btn_close.pack(side=tk.LEFT, padx=(8, 0))

        # Canvas for image
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.status = ttk.Label(self, text="", padding=(8, 6))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _load_image(self):
        if Image is None or ImageTk is None:
            messagebox.showerror(
                "Missing dependency",
                "Pillow is required to preview images in-app.\n\nInstall:\npython -m pip install pillow"
            )
            self.destroy()
            return

        try:
            self.status.config(text="Downloading...")
            self.update_idletasks()

            data = _download_bytes(self.url)
            img = Image.open(io.BytesIO(data))
            # Normalize for Tk rendering
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            self._pil_image = img

            self.status.config(text="")
            self._render_fit()

        except Exception as e:
            messagebox.showerror("Image load failed", str(e))
            self.destroy()

    def _render_fit(self):
        if self._pil_image is None:
            return

        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())

        img_w, img_h = self._pil_image.size
        scale = min(w / img_w, h / img_h)
        new_w = max(1, int(img_w * scale))
        new_h = max(1, int(img_h * scale))

        resized = self._pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.canvas.create_image(w // 2, h // 2, image=self._photo, anchor="center")

    def _toggle_fullscreen(self):
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)
        self.btn_fullscreen.config(text="Exit Fullscreen" if self._is_fullscreen else "Fullscreen")

    def _exit_fullscreen(self):
        if self._is_fullscreen:
            self._is_fullscreen = False
            self.attributes("-fullscreen", False)
            self.btn_fullscreen.config(text="Fullscreen")
