"""Identidad visual: paleta, tipografía y estilos de ttk."""

import ctypes
import sys
import tkinter as tk
from tkinter import font, ttk

LOMO = "#5A1F2B"
LOMO_SUAVE = "#6F3340"
LOMO_TEXTO = "#E6D3D7"
FONDO = "#F3F4F6"
SUPERFICIE = "#FFFFFF"
TINTA = "#23272E"
TENUE = "#68707A"
BORDE = "#DADDE2"
SELECCION = "#F0DDE1"
ALERTA = "#FFF1D2"
FILA_PAR = "#F9FAFB"


def activar_nitidez_windows() -> None:
    """Evita que Windows reescale la ventana borrosa; se llama antes de crear Tk."""
    if sys.platform == "win32":
        ctypes.windll.shcore.SetProcessDpiAwareness(1)


def _familia(raiz: tk.Tk, *preferidas: str) -> str:
    disponibles = set(font.families(raiz))
    return next((nombre for nombre in preferidas if nombre in disponibles), "TkDefaultFont")


def _plano(estilo: ttk.Style, nombre: str, fondo: str, activo: str, texto: str, **extra) -> None:
    estilo.configure(
        nombre, background=fondo, foreground=texto, bordercolor=fondo, lightcolor=fondo,
        darkcolor=fondo, focuscolor=texto, relief="flat", **extra,
    )
    estilo.map(
        nombre,
        background=[("disabled", BORDE), ("active", activo)],
        bordercolor=[("active", activo)], lightcolor=[("active", activo)], darkcolor=[("active", activo)],
    )


def _fuentes(raiz: tk.Tk) -> dict[str, font.Font]:
    cuerpo = _familia(raiz, "Segoe UI", "Noto Sans", "DejaVu Sans")
    titulos = _familia(raiz, "Georgia", "DejaVu Serif")
    for nombre in ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont"):
        font.nametofont(nombre, root=raiz).configure(family=cuerpo, size=10, weight="normal")
    fuentes = {
        "pagina": font.Font(root=raiz, family=titulos, size=20),
        "marca": font.Font(root=raiz, family=titulos, size=14),
        "seccion": font.Font(root=raiz, family=cuerpo, size=11, weight="bold"),
        "metrica": font.Font(root=raiz, family=titulos, size=17),
        "chica": font.Font(root=raiz, family=cuerpo, size=9),
        "cabecera": font.Font(root=raiz, family=cuerpo, size=9, weight="bold"),
    }
    raiz.fuentes = fuentes
    return fuentes


def _controles(estilo: ttk.Style) -> None:
    _plano(estilo, "TButton", SUPERFICIE, SELECCION, TINTA, padding=(12, 6))
    estilo.configure("TButton", bordercolor=BORDE)
    estilo.map("TButton", bordercolor=[("active", LOMO), ("focus", LOMO)])
    _plano(estilo, "Primario.TButton", LOMO, LOMO_SUAVE, SUPERFICIE, padding=(14, 6))
    estilo.map("Primario.TButton", foreground=[("disabled", TENUE)])

    campo = dict(fieldbackground=SUPERFICIE, background=SUPERFICIE, foreground=TINTA, bordercolor=BORDE,
                 lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, arrowcolor=TENUE, padding=5)
    for nombre in ("TEntry", "TCombobox", "TSpinbox"):
        estilo.configure(nombre, **campo)
        estilo.map(nombre, bordercolor=[("focus", LOMO)], fieldbackground=[("readonly", SUPERFICIE)],
                   selectbackground=[("readonly", SUPERFICIE)], selectforeground=[("readonly", TINTA)])


def _tablas(raiz: tk.Tk, estilo: ttk.Style, fuentes: dict) -> None:
    linea = font.nametofont("TkDefaultFont", root=raiz).metrics("linespace")
    estilo.configure("Treeview", background=SUPERFICIE, fieldbackground=SUPERFICIE, foreground=TINTA,
                     borderwidth=0, rowheight=linea + 12)
    estilo.map("Treeview", background=[("selected", SELECCION)], foreground=[("selected", TINTA)])
    estilo.configure("Treeview.Heading", background=SUPERFICIE, foreground=TENUE, relief="flat",
                     font=fuentes["cabecera"], padding=(6, 8), bordercolor=BORDE,
                     lightcolor=SUPERFICIE, darkcolor=BORDE)
    estilo.map("Treeview.Heading", background=[("active", FONDO)])
    estilo.layout("Vertical.TScrollbar", [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
        ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
    estilo.configure("Vertical.TScrollbar", troughcolor=SUPERFICIE, background=BORDE, bordercolor=SUPERFICIE,
                     lightcolor=BORDE, darkcolor=BORDE, arrowsize=10, relief="flat")
    estilo.map("Vertical.TScrollbar", background=[("active", TENUE)])


def _navegacion(estilo: ttk.Style, fuentes: dict) -> None:
    estilo.configure("Nav.TFrame", background=LOMO)
    estilo.configure("Marca.TLabel", background=LOMO, foreground=SUPERFICIE, font=fuentes["marca"])
    estilo.configure("NavSeccion.TLabel", background=LOMO, foreground=LOMO_TEXTO, font=fuentes["chica"])
    _plano(estilo, "Nav.TButton", LOMO, LOMO_SUAVE, SUPERFICIE, padding=(14, 7), anchor="w")
    _plano(estilo, "NavActiva.TButton", FONDO, FONDO, LOMO, padding=(14, 7), anchor="w")


def aplicar_tema(raiz: tk.Tk) -> None:
    fuentes = _fuentes(raiz)
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    raiz.configure(background=FONDO)
    estilo.configure(".", background=FONDO, foreground=TINTA)
    estilo.configure("Borde.TFrame", background=BORDE)
    estilo.configure("Pagina.TLabel", font=fuentes["pagina"])
    estilo.configure("Subtitulo.TLabel", foreground=TENUE)
    estilo.configure("Titulo.TLabel", font=fuentes["seccion"])
    estilo.configure("Campo.TLabel", foreground=TENUE, font=fuentes["chica"])
    estilo.configure("Metrica.TLabel", font=fuentes["metrica"])
    estilo.configure("Vacio.TLabel", background=SUPERFICIE, foreground=TENUE)
    _controles(estilo)
    _tablas(raiz, estilo, fuentes)
    _navegacion(estilo, fuentes)
    raiz.option_add("*TCombobox*Listbox.background", SUPERFICIE)
    raiz.option_add("*TCombobox*Listbox.foreground", TINTA)
    raiz.option_add("*TCombobox*Listbox.selectBackground", SELECCION)
    raiz.option_add("*TCombobox*Listbox.selectForeground", TINTA)
    raiz.option_add("*TCombobox*Listbox.borderWidth", 0)
