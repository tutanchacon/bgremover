"""
Diálogo "Acerca de".

Tres tabs: General, Dependencias, Licencia.
Se abre como ventana modal centrada sobre la ventana padre.
"""

import os
import sys
import webbrowser
import importlib
import customtkinter as ctk


def _get_version(module: str) -> str:
    try:
        m = importlib.import_module(module)
        return getattr(m, "__version__", "—")
    except ImportError:
        return "—"


def _get_version_pkg(pkg: str) -> str:
    try:
        from importlib.metadata import version
        return version(pkg)
    except Exception:
        return "—"


_VERSIONS = {
    "Python":         sys.version.split()[0],
    "BiRefNet/rembg": _get_version("rembg"),
    "ONNX Runtime":   _get_version("onnxruntime"),
    "Pillow":         _get_version("PIL"),
    "OpenCV":         _get_version("cv2"),
    "NumPy":          _get_version("numpy"),
    "CustomTkinter":  _get_version("customtkinter"),
    "TkinterDnD2":    _get_version_pkg("tkinterdnd2"),
}

_W = 520
_H = 460


class AboutDialog(ctk.CTkToplevel):
    """
    Ventana modal con tabs: General / Dependencias / Licencia.
    Solo puede haber una instancia abierta a la vez.
    """

    _instance: "AboutDialog | None" = None

    def __new__(cls, parent):
        if cls._instance is not None and cls._instance.winfo_exists():
            cls._instance.focus()
            cls._instance.lift()
            return cls._instance
        instance = super().__new__(cls)
        cls._instance = instance
        return instance

    def __init__(self, parent) -> None:
        if getattr(self, "_built", False):
            return
        self._built = True

        super().__init__(parent)
        self.title("Acerca de ClearCut")
        self.geometry(f"{_W}x{_H}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build()

        # Centrado después de que tkinter haya calculado las dimensiones reales
        self.after(10, lambda: self._center(parent))

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build(self) -> None:
        tabs = ctk.CTkTabview(self)
        tabs.grid(row=0, column=0, sticky="nsew", padx=16, pady=(12, 0))

        tabs.add("General")
        tabs.add("Dependencias")
        tabs.add("Licencia")

        self._build_general(tabs.tab("General"))
        self._build_versions(tabs.tab("Dependencias"))
        self._build_license(tabs.tab("Licencia"))

        ctk.CTkButton(
            self, text="Cerrar",
            command=self.destroy,
            width=120,
        ).grid(row=1, column=0, pady=(8, 16))

    # ── Tab General ───────────────────────────────────────────────────────────

    def _build_general(self, tab) -> None:
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab, text="✂  ClearCut",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, pady=(20, 2))

        ctk.CTkLabel(
            tab, text="Versión 1.0",
            text_color="gray", font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, pady=(0, 16))

        ctk.CTkLabel(
            tab,
            text=(
                "Eliminación profesional de fondos mediante inteligencia artificial.\n\n"
                "Usa BiRefNet — modelo de segmentación de última generación —\n"
                "para resultados de calidad comparable a remove.bg,\n"
                "completamente local y sin enviar tus imágenes a ningún servidor."
            ),
            font=ctk.CTkFont(size=12),
            justify="center",
        ).grid(row=2, column=0, padx=32, pady=(0, 24))

        ctk.CTkFrame(
            tab, height=1, fg_color=("gray75", "gray35")
        ).grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 16))

        ctk.CTkLabel(
            tab, text="Desarrollado por",
            text_color="gray", font=ctk.CTkFont(size=11),
        ).grid(row=4, column=0, pady=(0, 4))

        ctk.CTkLabel(
            tab, text="Marco Chacon",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=5, column=0, pady=(0, 12))

        links = ctk.CTkFrame(tab, fg_color="transparent")
        links.grid(row=6, column=0, pady=(0, 20))

        self._link_btn(links, "⌥  GitHub", "https://github.com/tutanchacon").pack(
            side="left", padx=12
        )
        self._link_btn(links, "⌂  tutansoft.com", "https://www.tutansoft.com").pack(
            side="left", padx=12
        )

    # ── Tab Dependencias ──────────────────────────────────────────────────────

    def _build_versions(self, tab) -> None:
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(tab)
        frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=12)
        frame.grid_columnconfigure(0, weight=1)

        for i, (name, ver) in enumerate(_VERSIONS.items()):
            row_bg = ("gray90", "gray17") if i % 2 == 0 else ("gray85", "gray20")

            row = ctk.CTkFrame(frame, fg_color=row_bg, corner_radius=4)
            row.pack(fill="x", pady=2, padx=4)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row, text=name,
                font=ctk.CTkFont(size=12), anchor="w",
            ).grid(row=0, column=0, padx=12, pady=6, sticky="w")

            ctk.CTkLabel(
                row, text=ver,
                font=ctk.CTkFont(size=12, family="Consolas"),
                text_color="gray", anchor="e",
            ).grid(row=0, column=1, padx=12, pady=6, sticky="e")

    # ── Tab Licencia ──────────────────────────────────────────────────────────

    def _build_license(self, tab) -> None:
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        box = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word",
        )
        box.grid(row=0, column=0, sticky="nsew", padx=8, pady=12)
        box.insert("1.0", self._load_license())
        box.configure(state="disabled")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_license(self) -> str:
        base = getattr(sys, "_MEIPASS", None) or os.path.dirname(
            os.path.abspath(sys.argv[0])
        )
        try:
            with open(os.path.join(base, "LICENSE.txt"), encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Archivo LICENSE.txt no encontrado."

    def _link_btn(self, parent, text: str, url: str) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            font=ctk.CTkFont(size=12, underline=True),
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            width=0,
            command=lambda: webbrowser.open(url),
        )

    def _center(self, parent) -> None:
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - _W) // 2
        y = parent.winfo_y() + (parent.winfo_height() - _H) // 2
        self.geometry(f"{_W}x{_H}+{x}+{y}")
