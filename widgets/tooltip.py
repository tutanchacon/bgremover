"""
Sistema de tooltips y HelpIcon.

Tooltip: comportamiento reutilizable que se puede adjuntar a cualquier widget.
HelpIcon: pequeño ícono "?" que muestra un Tooltip al hacer hover.

Diseñado para no acoplarse a ningún widget específico — cualquier
widget que acepte bind() puede tener un tooltip.
"""

import tkinter as tk
import customtkinter as ctk


class Tooltip:
    """
    Adjunta un tooltip a cualquier widget tkinter o customtkinter.

    El tooltip aparece después de un delay configurable y se posiciona
    automáticamente para no salir de la pantalla.
    """

    _DELAY_MS = 500
    _WRAP_PX  = 240
    _PAD_X    = 10
    _PAD_Y    = 6

    def __init__(self, widget: tk.BaseWidget, text: str) -> None:
        self._widget   = widget
        self._text     = text
        self._window   = None
        self._after_id = None

        widget.bind("<Enter>",       self._on_enter,  add="+")
        widget.bind("<Leave>",       self._on_leave,  add="+")
        widget.bind("<ButtonPress>", self._on_leave,  add="+")

    # ── Eventos ───────────────────────────────────────────────────────────────

    def _on_enter(self, _event=None) -> None:
        self._after_id = self._widget.after(self._DELAY_MS, self._show)

    def _on_leave(self, _event=None) -> None:
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        self._destroy()

    # ── Mostrar / ocultar ─────────────────────────────────────────────────────

    def _show(self) -> None:
        if self._window:
            return

        # Colores según el tema activo
        dark = ctk.get_appearance_mode() == "Dark"
        bg  = "#2b2b2b" if dark else "#f5f5f5"
        fg  = "#e8e8e8" if dark else "#1a1a1a"
        bd  = "#555555" if dark else "#cccccc"

        self._window = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)

        # Frame con borde sutil
        frame = tk.Frame(tw, background=bd, padx=1, pady=1)
        frame.pack(fill="both", expand=True)

        label = tk.Label(
            frame,
            text=self._text,
            justify="left",
            background=bg,
            foreground=fg,
            relief="flat",
            padx=self._PAD_X,
            pady=self._PAD_Y,
            wraplength=self._WRAP_PX,
            font=("Segoe UI", 9),
        )
        label.pack()

        tw.update_idletasks()
        self._position(tw)

    def _destroy(self) -> None:
        if self._window:
            self._window.destroy()
            self._window = None

    def _position(self, tw: tk.Toplevel) -> None:
        """Posiciona el tooltip debajo del widget, evitando que salga de pantalla."""
        w = self._widget
        tip_w = tw.winfo_width()
        tip_h = tw.winfo_height()

        # Punto de partida: centrado debajo del widget
        x = w.winfo_rootx() + w.winfo_width() // 2 - tip_w // 2
        y = w.winfo_rooty() + w.winfo_height() + 6

        # Corrección horizontal para no salir de pantalla
        screen_w = tw.winfo_screenwidth()
        if x + tip_w > screen_w - 8:
            x = screen_w - tip_w - 8
        if x < 8:
            x = 8

        # Corrección vertical: si no cabe abajo, lo pone arriba
        screen_h = tw.winfo_screenheight()
        if y + tip_h > screen_h - 8:
            y = w.winfo_rooty() - tip_h - 6

        tw.wm_geometry(f"+{x}+{y}")


class HelpIcon(ctk.CTkLabel):
    """
    Ícono circular "?" con tooltip integrado.
    Se usa junto a cualquier control para explicar su función.
    """

    def __init__(self, parent, help_text: str, **kwargs) -> None:
        super().__init__(
            parent,
            text="?",
            width=16,
            height=16,
            corner_radius=8,
            fg_color=("gray65", "gray45"),
            text_color=("gray15", "gray90"),
            font=ctk.CTkFont(size=10, weight="bold"),
            cursor="question_arrow",
            **kwargs,
        )
        Tooltip(self, help_text)
