#!/usr/bin/env python3
"""
BGRemover GUI — Entry point.

Compone SettingsPanel + PreviewPanel + controles de acción,
wirea los eventos y delega el procesamiento al engine.

La app no sabe nada de rembg ni de numpy — solo habla con
ProcessingEngine y con los widgets propios.
"""

import os
import threading
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk
from PIL import Image
from tkinterdnd2 import DND_FILES, TkinterDnD

from processing import ProcessingConfig, ProcessingEngine
from widgets import PreviewPanel, SettingsPanel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BGRemoverApp(ctk.CTk, TkinterDnD.DnDWrapper):
    """
    Ventana principal.

    Responsabilidades:
      - Componer y layoutear los paneles
      - Gestionar el estado de la sesión (ruta de entrada, resultado)
      - Delegar procesamiento al engine en un thread separado
      - Actualizar la UI con los callbacks del engine
    """

    TkdndVersion = None

    def __init__(self) -> None:
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self._engine = ProcessingEngine()
        self._input_path: Optional[str] = None
        self._result_image: Optional[Image.Image] = None

        self._build_window()
        self._build_ui()
        self._setup_drag_drop()

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build_window(self) -> None:
        self.title("BGRemover — BiRefNet")
        self.geometry("1120x680")
        self.resizable(False, False)
        # Columna 1 (área principal) crece; columna 0 (sidebar) es fija
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _build_ui(self) -> None:
        # ── Sidebar de configuración ──────────────────────────────────────────
        self._settings = SettingsPanel(self, width=220)
        self._settings.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

        # ── Área principal ────────────────────────────────────────────────────
        main = ctk.CTkFrame(self)
        main.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main.grid_columnconfigure((0, 1), weight=1)
        main.grid_rowconfigure(1, weight=1)

        # Encabezado
        ctk.CTkLabel(
            main, text="BGRemover",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(12, 0))
        ctk.CTkLabel(
            main, text="BiRefNet · calidad profesional · 100% local",
            font=ctk.CTkFont(size=11), text_color="gray",
        ).grid(row=0, column=0, columnspan=2, pady=(0, 0), sticky="s")

        # Previews
        self._preview_original = PreviewPanel(main, "Original")
        self._preview_original.grid(row=1, column=0, padx=(8, 4), pady=(48, 8), sticky="n")

        self._preview_result = PreviewPanel(main, "Resultado")
        self._preview_result.grid(row=1, column=1, padx=(4, 8), pady=(48, 8), sticky="n")

        # Controles de acción
        self._build_controls(main)

    def _build_controls(self, parent: ctk.CTkFrame) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 12))
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._btn_open = ctk.CTkButton(
            frame, text="Abrir imagen",
            command=self._select_file, width=160,
        )
        self._btn_open.grid(row=0, column=0, padx=8)

        self._btn_process = ctk.CTkButton(
            frame, text="Eliminar fondo",
            command=self._start_processing, width=160,
            state="disabled",
            fg_color="#2a7d4f", hover_color="#1e5c3a",
        )
        self._btn_process.grid(row=0, column=1, padx=8)

        self._btn_save = ctk.CTkButton(
            frame, text="Guardar PNG",
            command=self._save_result, width=160,
            state="disabled",
        )
        self._btn_save.grid(row=0, column=2, padx=8)

        bottom = ctk.CTkFrame(parent, fg_color="transparent")
        bottom.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        bottom.grid_columnconfigure(0, weight=1)

        self._progress = ctk.CTkProgressBar(bottom)
        self._progress.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self._progress.set(0)

        self._lbl_status = ctk.CTkLabel(
            bottom, text="Listo",
            text_color="gray", font=ctk.CTkFont(size=11),
        )
        self._lbl_status.grid(row=1, column=0)

    # ── Drag & drop ───────────────────────────────────────────────────────────

    def _setup_drag_drop(self) -> None:
        label = self._preview_original.get_label()
        label.drop_target_register(DND_FILES)
        label.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event) -> None:
        # tkinterdnd2 envuelve rutas con espacios entre llaves
        path = event.data.strip().strip("{}")
        self._load_image(path)

    # ── Carga de imagen ───────────────────────────────────────────────────────

    def _select_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if path:
            self._load_image(path)

    def _load_image(self, path: str) -> None:
        if not os.path.isfile(path):
            self._set_status("Archivo no válido", error=True)
            return

        self._input_path = path
        self._result_image = None
        self._progress.set(0)
        self._btn_save.configure(state="disabled")

        img = Image.open(path).convert("RGBA")
        self._preview_original.set_image(img)
        self._preview_result.set_placeholder("Aquí aparecerá\nel resultado")
        self._btn_process.configure(state="normal")
        self._set_status(f"Cargado: {os.path.basename(path)}")

    # ── Procesamiento ─────────────────────────────────────────────────────────

    def _start_processing(self) -> None:
        self._set_buttons_enabled(False)
        self._progress.configure(mode="indeterminate")
        self._progress.start()
        self._preview_result.set_placeholder("Procesando...")

        config = self._settings.get_config()
        threading.Thread(
            target=self._run_in_thread,
            args=(config,),
            daemon=True,
        ).start()

    def _run_in_thread(self, config: ProcessingConfig) -> None:
        """Corro la inferencia fuera del hilo principal para no congelar la UI."""
        try:
            with open(self._input_path, "rb") as f:
                input_data = f.read()

            result = self._engine.process(
                input_data,
                config,
                on_progress=lambda msg: self.after(0, lambda m=msg: self._set_status(m)),
            )
            self.after(0, lambda: self._on_success(result))

        except Exception as exc:
            self.after(0, lambda: self._on_error(str(exc)))

    def _on_success(self, result: Image.Image) -> None:
        self._result_image = result
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._progress.set(1)
        self._preview_result.set_image(result)
        self._set_status("Listo")
        self._set_buttons_enabled(True)
        self._btn_save.configure(state="normal")

    def _on_error(self, msg: str) -> None:
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._progress.set(0)
        self._preview_result.set_placeholder("Error al procesar")
        self._set_status(f"Error: {msg}", error=True)
        self._set_buttons_enabled(True)

    # ── Guardado ──────────────────────────────────────────────────────────────

    def _save_result(self) -> None:
        if not self._result_image:
            return

        base = os.path.splitext(os.path.basename(self._input_path))[0]
        # El formato depende del fondo elegido: PNG si hay alpha, JPEG si no
        has_alpha = self._result_image.mode == "RGBA"
        ext = ".png" if has_alpha else ".jpg"
        filetypes = (
            [("PNG con transparencia", "*.png")]
            if has_alpha
            else [("JPEG", "*.jpg")]
        )

        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            initialfile=f"{base}_sin_fondo{ext}",
            filetypes=filetypes,
        )
        if path:
            self._result_image.save(path)
            self._set_status(f"Guardado: {os.path.basename(path)}")

    # ── Helpers de UI ─────────────────────────────────────────────────────────

    def _set_buttons_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._btn_open.configure(state=state)
        self._btn_process.configure(state=state)

    def _set_status(self, msg: str, error: bool = False) -> None:
        self._lbl_status.configure(
            text=msg,
            text_color="#e05555" if error else "gray",
        )


def main() -> None:
    app = BGRemoverApp()
    app.mainloop()


if __name__ == "__main__":
    main()
