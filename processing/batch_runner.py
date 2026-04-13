"""
Ejecutor de procesamiento en lote.

SRP: solo orquesta la iteración sobre archivos y delega en ProcessingEngine.
No sabe nada de UI — comunica su estado exclusivamente a través de callbacks.
El cancel_event permite cancelación limpia entre imágenes sin matar threads.
"""

import os
import threading
from dataclasses import dataclass
from typing import Callable, List, Optional

from .config import ProcessingConfig
from .engine import ProcessingEngine


@dataclass
class BatchCallbacks:
    """
    Contrato de comunicación entre BatchRunner y quien lo invoca.

    Todos los callbacks se invocan desde el thread del runner.
    El caller es responsable de despacharlos al hilo principal
    si necesita actualizar la UI (ej: self.after(0, ...)).
    """

    on_file_start: Callable[[int, str], None]
    # (índice 0-based, nombre de archivo)

    on_file_done: Callable[[int, str, bool, str], None]
    # (índice, nombre, éxito, mensaje de error)

    on_complete: Callable[[int, int], None]
    # (total procesados, cantidad de errores)

    on_progress: Optional[Callable[[str], None]] = None
    # Mensajes internos del engine (opcional — suele omitirse en batch)


class BatchRunner:
    """
    Procesa una lista de archivos secuencialmente usando ProcessingEngine.

    Es stateless: cada llamada a run() es independiente.
    Recibe el engine por parámetro para permitir reutilización de la sesión
    del modelo entre llamadas sucesivas.
    """

    def run(
        self,
        files: List[str],
        output_dir: str,
        config: ProcessingConfig,
        callbacks: BatchCallbacks,
        cancel_event: threading.Event,
        engine: ProcessingEngine,
    ) -> None:
        errors = 0

        for idx, filepath in enumerate(files):
            if cancel_event.is_set():
                break

            filename = os.path.basename(filepath)
            callbacks.on_file_start(idx, filename)

            try:
                with open(filepath, "rb") as f:
                    input_data = f.read()

                result = engine.process(
                    input_data,
                    config,
                    on_progress=callbacks.on_progress,
                )

                base = os.path.splitext(filename)[0]
                ext = ".png" if result.mode == "RGBA" else ".jpg"
                out_path = os.path.join(output_dir, f"{base}_sin_fondo{ext}")
                result.save(out_path)

                callbacks.on_file_done(idx, filename, True, "")

            except Exception as exc:
                errors += 1
                callbacks.on_file_done(idx, filename, False, str(exc))

        callbacks.on_complete(len(files), errors)
