#!/usr/bin/env python3
"""
BGRemover GUI — Entry point.

Shell mínimo que compone los paneles y los wirea.
No contiene lógica de negocio ni de procesamiento — solo construcción de UI.

Responsabilidades:
  - Crear el engine compartido (una sola carga del modelo para ambos modos)
  - Crear el SettingsPanel compartido
  - Componer SingleTab y BatchTab inyectando sus dependencias
"""

from tkinterdnd2 import TkinterDnD
import customtkinter as ctk

from processing import ProcessingEngine
from widgets import BatchTab, SettingsPanel, SingleTab

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BGRemoverApp(ctk.CTk, TkinterDnD.DnDWrapper):
    """Ventana principal. Compone sin implementar."""

    TkdndVersion = None

    def __init__(self) -> None:
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        # Engine compartido entre tabs — cachea la sesión del modelo
        self._engine = ProcessingEngine()

        self._build_window()
        self._build_ui()

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build_window(self) -> None:
        self.title("BGRemover — BiRefNet")
        self.geometry("1120x720")
        self.resizable(False, False)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _build_ui(self) -> None:
        # ── Sidebar compartido ────────────────────────────────────────────────
        self._settings = SettingsPanel(self, width=220)
        self._settings.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

        # ── Área principal ────────────────────────────────────────────────────
        main = ctk.CTkFrame(self)
        main.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self._build_header(main)
        self._build_tabs(main)

    def _build_header(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            parent, text="BGRemover",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, pady=(12, 0))

        ctk.CTkLabel(
            parent,
            text="BiRefNet · calidad profesional · 100% local",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).grid(row=0, column=0, sticky="s", pady=(0, 2))

    def _build_tabs(self, parent: ctk.CTkFrame) -> None:
        tabview = ctk.CTkTabview(parent)
        tabview.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 8))
        tabview.add("Individual")
        tabview.add("Batch")

        # ── Tab individual ────────────────────────────────────────────────────
        tab_single = tabview.tab("Individual")
        tab_single.grid_columnconfigure(0, weight=1)
        tab_single.grid_rowconfigure(0, weight=1)

        SingleTab(
            tab_single,
            engine=self._engine,
            get_config=self._settings.get_config,
        ).grid(row=0, column=0, sticky="nsew")

        # ── Tab batch ─────────────────────────────────────────────────────────
        tab_batch = tabview.tab("Batch")
        tab_batch.grid_columnconfigure(0, weight=1)
        tab_batch.grid_rowconfigure(0, weight=1)

        BatchTab(
            tab_batch,
            engine=self._engine,
            get_config=self._settings.get_config,
        ).grid(row=0, column=0, sticky="nsew")


def main() -> None:
    app = BGRemoverApp()
    app.mainloop()


if __name__ == "__main__":
    main()
