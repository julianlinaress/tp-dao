"""Apariencia de la interfaz según el sistema operativo."""

import ctypes
import sys
import tkinter as tk
from tkinter import font, ttk


def activar_nitidez_windows() -> None:
    """Evita que Windows reescale la ventana borrosa; se llama antes de crear Tk."""
    if sys.platform == "win32":
        ctypes.windll.shcore.SetProcessDpiAwareness(1)


def aplicar_tema(raiz: tk.Tk) -> None:
    estilo = ttk.Style(raiz)
    estilo.theme_use("vista" if "vista" in estilo.theme_names() else "clam")

    base = font.nametofont("TkDefaultFont")
    estilo.configure("Treeview", rowheight=base.metrics("linespace") + 8)
    titulo = base.copy()
    titulo.configure(weight="bold")
    raiz.fuente_titulo = titulo
    estilo.configure("Titulo.TLabel", font=titulo)
