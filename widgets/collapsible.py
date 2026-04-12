"""
Frame colapsable con header clicable.

Permite agrupar controles avanzados que no necesitan estar
siempre visibles, sin perder acceso rápido a ellos.
"""

import customtkinter as ctk


class CollapsibleFrame(ctk.CTkFrame):
    """
    Frame con un header-botón que expande o colapsa el contenido.
    Los widgets hijo deben colocarse dentro de .body.
    """

    def __init__(
        self,
        parent,
        title: str,
        expanded: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._title = title
        self._expanded = expanded

        self._header = ctk.CTkButton(
            self,
            text=self._header_text(),
            anchor="w",
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle,
        )
        self._header.grid(row=0, column=0, sticky="ew", padx=4, pady=(6, 0))

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 6))
        self._body.grid_columnconfigure(0, weight=1)

        if not expanded:
            self._body.grid_remove()

    @property
    def body(self) -> ctk.CTkFrame:
        """Contenedor donde colocar los widgets hijo."""
        return self._body

    # ── Privados ──────────────────────────────────────────────────────────────

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self._header.configure(text=self._header_text())
        if self._expanded:
            self._body.grid()
        else:
            self._body.grid_remove()

    def _header_text(self) -> str:
        arrow = "▼" if self._expanded else "▶"
        return f"  {arrow}  {self._title}"
