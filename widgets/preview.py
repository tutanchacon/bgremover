"""
Panel de previsualización de imagen.

Responsabilidad única: mostrar una imagen con título, manteniendo
proporción y superponiendo un tablero de ajedrez para visualizar
la transparencia del canal alpha.
"""

import customtkinter as ctk
import numpy as np
from PIL import Image


class PreviewPanel(ctk.CTkFrame):
    """
    Widget reutilizable que muestra una imagen o un placeholder de texto.
    Expone get_label() para que el caller pueda registrar drag & drop.
    """

    _W = 400
    _H = 380

    def __init__(self, parent, title: str, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)

        ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(weight="bold")
        ).pack()

        self._label = ctk.CTkLabel(
            self, text="",
            width=self._W, height=self._H,
            fg_color=("gray85", "gray20"),
            corner_radius=8,
        )
        self._label.pack(padx=4, pady=4)

        # Imagen transparente 1×1 que usamos como "sin imagen".
        # Nunca pasamos image=None a customtkinter porque no limpia el registro
        # interno del widget Tk subyacente, lo que provoca TclError al redibujar.
        _transparent = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        self._blank = ctk.CTkImage(
            light_image=_transparent,
            dark_image=_transparent,
            size=(1, 1),
        )

        # Referencia activa a la CTkImage actual (evita que el GC la destruya)
        self._ctk_image: ctk.CTkImage = self._blank

        self.set_placeholder("Arrastrá una imagen\no usá el botón")

    # ── Interfaz pública ──────────────────────────────────────────────────────

    def set_image(self, img: Image.Image) -> None:
        """Muestra img escalada al tamaño máximo del panel."""
        display = img.copy()
        display.thumbnail((self._W, self._H), Image.Resampling.LANCZOS)

        if display.mode == "RGBA":
            canvas = self._make_checker(display.size)
            canvas.paste(display, mask=display.split()[3])
            display = canvas

        new_image = ctk.CTkImage(
            light_image=display,
            dark_image=display,
            size=display.size,
        )
        # Actualizamos la referencia ANTES de configure para que la imagen anterior
        # no sea elegible para GC mientras customtkinter procesa el redibujado.
        self._ctk_image = new_image
        self._label.configure(image=new_image, text="")

    def set_placeholder(self, text: str) -> None:
        # Usamos _blank en lugar de None para evitar el bug de customtkinter
        # donde el widget Tk interno retiene el nombre del PhotoImage anterior
        # y falla al validar la configuración en el siguiente redibujado.
        self._ctk_image = self._blank
        self._label.configure(image=self._blank, text=text, text_color="gray")

    def get_label(self) -> ctk.CTkLabel:
        """Expone el label interno para registrar drag & drop externamente."""
        return self._label

    # ── Helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def _make_checker(size: tuple, tile: int = 14) -> Image.Image:
        """Genera un tablero de ajedrez como fondo para visualizar la transparencia."""
        w, h = size
        xs = np.arange(w) // tile
        ys = np.arange(h) // tile
        pattern = ((xs[None, :] + ys[:, None]) % 2).astype(np.uint8)
        arr = np.where(
            pattern[:, :, None],
            np.array([160, 160, 160], dtype=np.uint8),
            np.array([205, 205, 205], dtype=np.uint8),
        )
        return Image.fromarray(arr, "RGB")
