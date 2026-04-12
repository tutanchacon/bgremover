"""
Panel lateral de configuración.

Responsabilidad única: presentar los controles de ajuste y devolver
un ProcessingConfig listo para usar — sin saber nada de cómo se procesa.

Compone CollapsibleFrame, LabeledSlider y HelpIcon para organizar los
controles en secciones expandibles con ayuda contextual integrada.
"""

import customtkinter as ctk
from typing import Tuple

from .collapsible import CollapsibleFrame
from .slider import LabeledSlider
from .tooltip import HelpIcon, Tooltip
from processing.config import (
    ProcessingConfig,
    AVAILABLE_MODELS,
    BACKGROUND_OPTIONS,
)

# ── Textos de ayuda ───────────────────────────────────────────────────────────
# Los centralizo aquí para facilitar su edición sin tocar la lógica de UI.

_HELP = {
    "model": (
        "Elige el modelo según el contenido de la imagen:\n\n"
        "• BiRefNet General — mejor calidad para cualquier imagen\n"
        "• BiRefNet Portrait — optimizado para personas y retratos\n"
        "• BiRefNet Lite — más rápido, calidad ligeramente menor\n"
        "• U2Net Personas — muy rápido para siluetas humanas\n"
        "• ISNet General — bueno para objetos y productos"
    ),
    "alpha_matting": (
        "Mejora la calidad de los bordes en zonas de transición "
        "como el cabello, pelaje o telas.\n\n"
        "Activado: bordes más suaves y naturales, proceso más lento.\n"
        "Desactivado: bordes más definidos, proceso más rápido."
    ),
    "fg_threshold": (
        "Define qué tan agresivo es el modelo al conservar píxeles "
        "como parte del sujeto.\n\n"
        "Valores altos (≥240): conserva más píxeles, ideal para "
        "sujetos con detalles finos como cabello.\n"
        "Valores bajos: más restrictivo, descarta más píxeles del borde."
    ),
    "bg_threshold": (
        "Define qué tan agresivo es el modelo al eliminar píxeles "
        "como parte del fondo.\n\n"
        "Valores bajos (≤30): conservador, mantiene más del sujeto.\n"
        "Valores altos: elimina más agresivamente el fondo."
    ),
    "erode_size": (
        "Tamaño del kernel de erosión aplicado al borde antes del matting.\n\n"
        "Valores altos: elimina más del borde exterior, útil cuando "
        "quedan restos del fondo.\n"
        "Valor 0: sin erosión."
    ),
    "alpha_cleanup": (
        "Elimina transparencias parciales residuales que el modelo "
        "dejó sin definir.\n\n"
        "Píxeles con alpha menor al umbral → completamente transparentes.\n"
        "Píxeles con alpha mayor al umbral → completamente opacos.\n"
        "Valor 0: desactivado."
    ),
    "edge_smooth": (
        "Aplica un suavizado gaussiano al canal alpha solo sobre los "
        "píxeles de borde.\n\n"
        "Valores altos: bordes más suaves pero potencialmente menos precisos.\n"
        "Valor 0: desactivado."
    ),
    "background": (
        "Fondo que se aplica sobre la transparencia al guardar:\n\n"
        "• Transparente — PNG con canal alpha (recomendado)\n"
        "• Blanco / Negro — fondo sólido, se guarda como JPG\n"
        "• Personalizado — elegí cualquier color"
    ),
}


class SettingsPanel(ctk.CTkScrollableFrame):
    """
    Panel de configuración completo con secciones colapsables:
      - Modelo AI
      - Alpha Matting (foreground, background, erode)
      - Post-procesamiento (limpieza de alpha, suavizado de bordes)
      - Fondo de salida (transparente, blanco, negro, personalizado)
    """

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, label_text="  Configuración", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._bg_color: Tuple[int, int, int] = (255, 255, 255)
        self._model_keys = list(AVAILABLE_MODELS.keys())
        self._model_names = list(AVAILABLE_MODELS.values())
        self._bg_keys = list(BACKGROUND_OPTIONS.keys())
        self._bg_names = list(BACKGROUND_OPTIONS.values())

        self._build()

    # ── Interfaz pública ──────────────────────────────────────────────────────

    def get_config(self) -> ProcessingConfig:
        """Devuelve la configuración actual como dataclass — única salida del panel."""
        return ProcessingConfig(
            model=self._model_keys[self._model_names.index(self._var_model.get())],
            alpha_matting=self._var_alpha_matting.get(),
            alpha_matting_foreground_threshold=int(self._sl_fg.get()),
            alpha_matting_background_threshold=int(self._sl_bg.get()),
            alpha_matting_erode_size=int(self._sl_erode.get()),
            post_alpha_cleanup=int(self._sl_cleanup.get()),
            post_edge_smooth=round(self._sl_smooth.get(), 1),
            background=self._bg_keys[self._bg_names.index(self._var_bg.get())],
            background_color=self._bg_color,
        )

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_model_section()
        self._separator()
        self._build_alpha_matting_section()
        self._separator()
        self._build_postprocess_section()
        self._separator()
        self._build_background_section()

    def _build_model_section(self) -> None:
        section = CollapsibleFrame(self, title="Modelo AI", expanded=True)
        section.pack(fill="x", pady=(0, 2))

        # Fila: label + help icon
        row = ctk.CTkFrame(section.body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            row, text="Modelo", font=ctk.CTkFont(size=11), text_color="gray",
        ).pack(side="left")
        HelpIcon(row, _HELP["model"]).pack(side="left", padx=(4, 0))

        self._var_model = ctk.StringVar(value=self._model_names[0])
        self._opt_model = ctk.CTkOptionMenu(
            section.body,
            variable=self._var_model,
            values=self._model_names,
            width=195,
            dynamic_resizing=False,
        )
        self._opt_model.pack(fill="x")

    def _build_alpha_matting_section(self) -> None:
        section = CollapsibleFrame(self, title="Alpha Matting", expanded=True)
        section.pack(fill="x", pady=(0, 2))

        # Toggle con help icon
        toggle_row = ctk.CTkFrame(section.body, fg_color="transparent")
        toggle_row.pack(fill="x", pady=(0, 8))
        toggle_row.grid_columnconfigure(0, weight=1)

        label_row = ctk.CTkFrame(toggle_row, fg_color="transparent")
        label_row.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(label_row, text="Activado").pack(side="left")
        HelpIcon(label_row, _HELP["alpha_matting"]).pack(side="left", padx=(4, 0))

        self._var_alpha_matting = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            toggle_row, text="",
            variable=self._var_alpha_matting,
            command=self._on_alpha_matting_toggle,
        ).grid(row=0, column=1)

        # Sliders con help icons
        self._sl_fg = LabeledSlider(
            section.body, "Foreground",
            from_=0, to=300, initial=290, step=1,
            help_text=_HELP["fg_threshold"],
        )
        self._sl_fg.pack(fill="x", pady=2)

        self._sl_bg = LabeledSlider(
            section.body, "Background",
            from_=0, to=255, initial=30, step=1,
            help_text=_HELP["bg_threshold"],
        )
        self._sl_bg.pack(fill="x", pady=2)

        self._sl_erode = LabeledSlider(
            section.body, "Erode size",
            from_=0, to=40, initial=3, step=1,
            help_text=_HELP["erode_size"],
        )
        self._sl_erode.pack(fill="x", pady=2)

        self._alpha_sliders = [self._sl_fg, self._sl_bg, self._sl_erode]

    def _build_postprocess_section(self) -> None:
        section = CollapsibleFrame(self, title="Post-procesamiento", expanded=False)
        section.pack(fill="x", pady=(0, 2))

        self._sl_cleanup = LabeledSlider(
            section.body, "Limpieza α",
            from_=0, to=100, initial=0, step=1,
            help_text=_HELP["alpha_cleanup"],
        )
        self._sl_cleanup.pack(fill="x", pady=2)

        self._sl_smooth = LabeledSlider(
            section.body, "Suavizado",
            from_=0.0, to=5.0, initial=0.0, step=0.1, fmt="{:.1f}",
            help_text=_HELP["edge_smooth"],
        )
        self._sl_smooth.pack(fill="x", pady=(8, 2))

    def _build_background_section(self) -> None:
        section = CollapsibleFrame(self, title="Fondo de salida", expanded=False)
        section.pack(fill="x", pady=(0, 2))

        # Fila: label + help icon
        row = ctk.CTkFrame(section.body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            row, text="Fondo", font=ctk.CTkFont(size=11), text_color="gray",
        ).pack(side="left")
        HelpIcon(row, _HELP["background"]).pack(side="left", padx=(4, 0))

        self._var_bg = ctk.StringVar(value=self._bg_names[0])
        ctk.CTkOptionMenu(
            section.body,
            variable=self._var_bg,
            values=self._bg_names,
            command=self._on_bg_change,
            width=195,
            dynamic_resizing=False,
        ).pack(fill="x", pady=(0, 6))

        self._btn_color = ctk.CTkButton(
            section.body,
            text="Elegir color...",
            command=self._pick_color,
            width=195,
        )
        # Solo aparece cuando se elige "Personalizado"

    def _separator(self) -> None:
        ctk.CTkFrame(
            self, height=1, fg_color=("gray75", "gray35")
        ).pack(fill="x", padx=8, pady=2)

    # ── Eventos ───────────────────────────────────────────────────────────────

    def _on_alpha_matting_toggle(self) -> None:
        enabled = self._var_alpha_matting.get()
        for slider in self._alpha_sliders:
            slider.set_enabled(enabled)

    def _on_bg_change(self, display_name: str) -> None:
        if display_name == BACKGROUND_OPTIONS["custom"]:
            self._btn_color.pack(fill="x")
        else:
            self._btn_color.pack_forget()

    def _pick_color(self) -> None:
        from tkinter import colorchooser
        hex_initial = "#{:02x}{:02x}{:02x}".format(*self._bg_color)
        result = colorchooser.askcolor(color=hex_initial, title="Elegir color de fondo")
        if result[0]:
            self._bg_color = tuple(int(c) for c in result[0])
            hex_color = result[1]
            self._btn_color.configure(
                text=f"Color: {hex_color}",
                fg_color=hex_color,
                hover_color=hex_color,
            )
