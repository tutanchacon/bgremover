"""
Tab de procesamiento en lote.

Responsabilidad única: gestionar la UI del modo batch y coordinar
BatchRunner + ProcessingEngine. No sabe nada de cómo funciona el modelo.

Comunicación con el runner:
  - BatchRunner corre en un thread secundario
  - Los callbacks envuelven toda actualización de UI en self.after(0, ...)
    para garantizar que se ejecuten en el hilo principal de Tkinter.
"""

import os
import threading
from tkinter import filedialog
from typing import Callable, List, Optional

import customtkinter as ctk

from processing import ProcessingConfig, ProcessingEngine
from processing.batch_runner import BatchCallbacks, BatchRunner

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}


def _scan_images(folder: str) -> List[str]:
    """Retorna rutas absolutas de imágenes en folder, ordenadas por nombre."""
    return sorted(
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.splitext(f.lower())[1] in _IMAGE_EXTS
    )


class BatchTab(ctk.CTkFrame):
    """
    Panel de procesamiento en lote con selección de carpetas,
    log de progreso por archivo y cancelación limpia.
    """

    def __init__(
        self,
        parent,
        engine: ProcessingEngine,
        get_config: Callable[[], ProcessingConfig],
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._engine = engine
        self._get_config = get_config
        self._runner = BatchRunner()
        self._cancel_event = threading.Event()
        self._files: List[str] = []
        self._input_folder: Optional[str] = None
        self._output_folder: Optional[str] = None
        self._is_running = False
        self._current_log_line = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # el log ocupa el espacio restante

        self._build()

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_folder_section()
        self._build_file_count()
        self._build_log()
        self._build_progress_section()
        self._build_action_buttons()

    def _build_folder_section(self) -> None:
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        frame.grid_columnconfigure(1, weight=1)

        for row_idx, (label, attr_btn) in enumerate([
            ("Entrada:", "_btn_input"),
            ("Salida:",  "_btn_output"),
        ]):
            pady = (10, 4) if row_idx == 0 else (4, 10)

            ctk.CTkLabel(frame, text=label, width=70, anchor="w").grid(
                row=row_idx, column=0, padx=(12, 6), pady=pady, sticky="w"
            )

            lbl = ctk.CTkLabel(
                frame, text="Sin seleccionar",
                anchor="w", text_color="gray",
                fg_color=("gray85", "gray20"), corner_radius=6,
            )
            lbl.grid(row=row_idx, column=1, padx=(0, 6), pady=pady, sticky="ew")

            cmd = self._select_input_folder if row_idx == 0 else self._select_output_folder
            ctk.CTkButton(
                frame, text="Elegir...", width=80, command=cmd,
            ).grid(row=row_idx, column=2, padx=(0, 12), pady=pady)

            # Guardo la referencia al label de ruta
            if row_idx == 0:
                self._lbl_input_path = lbl
            else:
                self._lbl_output_path = lbl

    def _build_file_count(self) -> None:
        self._lbl_file_count = ctk.CTkLabel(
            self,
            text="Seleccioná una carpeta de entrada",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        )
        self._lbl_file_count.grid(row=1, column=0, pady=(0, 4))

    def _build_log(self) -> None:
        self._log = ctk.CTkTextbox(
            self,
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self._log.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 4))

    def _build_progress_section(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 4))
        frame.grid_columnconfigure(0, weight=1)

        self._progress = ctk.CTkProgressBar(frame)
        self._progress.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self._progress.set(0)

        self._lbl_status = ctk.CTkLabel(
            frame, text="Listo",
            text_color="gray", font=ctk.CTkFont(size=11),
        )
        self._lbl_status.grid(row=1, column=0)

    def _build_action_buttons(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=4, column=0, pady=(0, 12))

        self._btn_process = ctk.CTkButton(
            frame, text="Procesar batch",
            command=self._start_batch,
            width=180, state="disabled",
            fg_color="#2a7d4f", hover_color="#1e5c3a",
        )
        self._btn_process.grid(row=0, column=0, padx=8)

        self._btn_cancel = ctk.CTkButton(
            frame, text="Cancelar",
            command=self._cancel_batch,
            width=120, state="disabled",
            fg_color="#7d2a2a", hover_color="#5c1e1e",
        )
        self._btn_cancel.grid(row=0, column=1, padx=8)

    # ── Selección de carpetas ─────────────────────────────────────────────────

    def _select_input_folder(self) -> None:
        folder = filedialog.askdirectory(title="Seleccionar carpeta de entrada")
        if not folder:
            return

        self._input_folder = folder
        self._files = _scan_images(folder)
        self._lbl_input_path.configure(
            text=folder, text_color=("gray10", "gray90")
        )

        n = len(self._files)
        if n == 0:
            self._lbl_file_count.configure(
                text="No se encontraron imágenes en esa carpeta",
                text_color="#e05555",
            )
        else:
            plural = "s" if n != 1 else ""
            self._lbl_file_count.configure(
                text=f"{n} imagen{plural} encontrada{plural}",
                text_color=("gray10", "gray90"),
            )

        self._refresh_process_button()

    def _select_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if not folder:
            return

        self._output_folder = folder
        self._lbl_output_path.configure(
            text=folder, text_color=("gray10", "gray90")
        )
        self._refresh_process_button()

    def _refresh_process_button(self) -> None:
        can_start = (
            bool(self._input_folder)
            and bool(self._output_folder)
            and len(self._files) > 0
            and not self._is_running
        )
        self._btn_process.configure(state="normal" if can_start else "disabled")

    # ── Batch processing ──────────────────────────────────────────────────────

    def _start_batch(self) -> None:
        self._is_running = True
        self._cancel_event.clear()
        self._log_clear()
        self._progress.set(0)
        self._btn_process.configure(state="disabled")
        self._btn_cancel.configure(state="normal")
        self._set_status(f"Iniciando — {len(self._files)} archivos...")

        config = self._get_config()
        callbacks = BatchCallbacks(
            on_file_start=lambda i, n: self.after(
                0, lambda i=i, n=n: self._on_file_start(i, n)
            ),
            on_file_done=lambda i, n, ok, err: self.after(
                0, lambda i=i, n=n, ok=ok, err=err: self._on_file_done(i, n, ok, err)
            ),
            on_complete=lambda t, e: self.after(
                0, lambda t=t, e=e: self._on_complete(t, e)
            ),
        )

        threading.Thread(
            target=self._runner.run,
            args=(
                self._files,
                self._output_folder,
                config,
                callbacks,
                self._cancel_event,
                self._engine,
            ),
            daemon=True,
        ).start()

    def _cancel_batch(self) -> None:
        self._cancel_event.set()
        self._btn_cancel.configure(state="disabled")
        self._set_status("Cancelando — esperando que termine el archivo actual...")

    # ── Callbacks del runner (ya en el hilo principal vía after) ─────────────

    def _on_file_start(self, idx: int, filename: str) -> None:
        total = len(self._files)
        self._set_status(f"Procesando {idx + 1} de {total}: {filename}")
        self._progress.set(idx / total)
        self._current_log_line = self._log_append(f"⟳  {filename}")

    def _on_file_done(self, idx: int, filename: str, success: bool, error: str) -> None:
        if success:
            self._log_replace_line(self._current_log_line, f"✓  {filename}")
        else:
            self._log_replace_line(
                self._current_log_line, f"✗  {filename}  —  {error}"
            )

    def _on_complete(self, total: int, errors: int) -> None:
        self._is_running = False
        self._progress.set(1)
        self._btn_cancel.configure(state="disabled")
        self._refresh_process_button()

        cancelled = self._cancel_event.is_set()
        processed = total - errors if not cancelled else self._current_log_line

        if cancelled:
            self._set_status(
                f"Cancelado. {processed} procesadas, {errors} errores."
            )
        elif errors:
            self._set_status(
                f"Completado con {errors} error{'es' if errors != 1 else ''}. "
                f"{total - errors} de {total} correctas."
            )
        else:
            self._set_status(f"Completado. {total} archivos procesados sin errores.")

    # ── Helpers de log ────────────────────────────────────────────────────────

    def _log_clear(self) -> None:
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        self._current_log_line = 0

    def _log_append(self, text: str) -> int:
        """Agrega una línea al log y retorna su número (base 1) para poder editarla."""
        self._log.configure(state="normal")
        self._current_log_line += 1
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")
        return self._current_log_line

    def _log_replace_line(self, line: int, text: str) -> None:
        """Reemplaza el contenido de una línea del log sin alterar el resto."""
        self._log.configure(state="normal")
        self._log.delete(f"{line}.0", f"{line}.end")
        self._log.insert(f"{line}.0", text)
        self._log.see("end")
        self._log.configure(state="disabled")

    # ── Helper de status ──────────────────────────────────────────────────────

    def _set_status(self, msg: str, error: bool = False) -> None:
        self._lbl_status.configure(
            text=msg,
            text_color="#e05555" if error else "gray",
        )
