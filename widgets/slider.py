"""
Slider con etiqueta y valor numérico.

Layout de dos filas para maximizar el ancho físico del slider
independientemente del valor máximo o del ancho del panel contenedor:

  Fila 0:  [Etiqueta .............. Valor][?]
  Fila 1:  [========= slider ============]
"""

import customtkinter as ctk
from typing import Callable, Optional
from .tooltip import HelpIcon


class LabeledSlider(ctk.CTkFrame):
    """
    Slider que ocupa el ancho completo disponible.
    La etiqueta, el valor actual y el HelpIcon van en la fila superior;
    el track del slider ocupa toda la fila inferior.
    """

    def __init__(
        self,
        parent,
        label: str,
        from_: float,
        to: float,
        initial: float,
        step: float = 1.0,
        fmt: str = "{:.0f}",
        help_text: str = "",
        on_change: Optional[Callable[[float], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._fmt = fmt
        self._on_change = on_change

        # ── Fila 0: etiqueta (izq) · valor + help (der) ───────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self._lbl_name = ctk.CTkLabel(
            header, text=label,
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        self._lbl_name.grid(row=0, column=0, sticky="w")

        self._lbl_value = ctk.CTkLabel(
            header,
            text=fmt.format(initial),
            font=ctk.CTkFont(size=11),
            anchor="e",
            width=36,
        )
        self._lbl_value.grid(row=0, column=1, padx=(4, 0))

        if help_text:
            HelpIcon(header, help_text).grid(row=0, column=2, padx=(4, 0))

        # ── Fila 1: slider a ancho completo ───────────────────────────────────
        steps = max(1, int(round((to - from_) / step)))
        self._slider = ctk.CTkSlider(
            self,
            from_=from_,
            to=to,
            number_of_steps=steps,
            command=self._on_slider_move,
        )
        self._slider.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self._slider.set(initial)

    # ── Interfaz pública ──────────────────────────────────────────────────────

    def get(self) -> float:
        return self._slider.get()

    def set(self, value: float) -> None:
        self._slider.set(value)
        self._lbl_value.configure(text=self._fmt.format(value))

    def set_enabled(self, enabled: bool) -> None:
        """Habilita o deshabilita visualmente el slider completo."""
        state = "normal" if enabled else "disabled"
        color = ("gray10", "gray90") if enabled else "gray50"
        self._slider.configure(state=state)
        self._lbl_name.configure(text_color=color)
        self._lbl_value.configure(text_color=color)

    # ── Privados ──────────────────────────────────────────────────────────────

    def _on_slider_move(self, value: float) -> None:
        self._lbl_value.configure(text=self._fmt.format(value))
        if self._on_change:
            self._on_change(value)
