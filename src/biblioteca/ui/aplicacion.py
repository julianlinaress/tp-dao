"""Ventana principal."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from biblioteca.datos_ejemplo import CargaEjemplo
from biblioteca.ui.pantallas.catalogo import (
    PantallaDisponibilidad,
    PantallaEjemplares,
    PantallaLibros,
)
from biblioteca.ui.pantallas.logistica import PantallaLogistica
from biblioteca.ui.pantallas.prestamos import PantallaMultas, PantallaPrestamos
from biblioteca.ui.pantallas.reportes import PantallaReportes
from biblioteca.ui.pantallas.reservas import PantallaReservas
from biblioteca.ui.pantallas.sedes import PantallaSedes
from biblioteca.ui.pantallas.socios import PantallaSocios

PANTALLAS = [
    ("Préstamos", PantallaPrestamos),
    ("Logística", PantallaLogistica),
    ("Reservas", PantallaReservas),
    ("Disponibilidad", PantallaDisponibilidad),
    ("Multas", PantallaMultas),
    ("Socios", PantallaSocios),
    ("Libros", PantallaLibros),
    ("Ejemplares", PantallaEjemplares),
    ("Sedes", PantallaSedes),
    ("Reportes", PantallaReportes),
]


class Aplicacion(tk.Tk):
    def __init__(self, servicios, ruta: Path) -> None:
        super().__init__()
        self.title("Sistema de Préstamos Interbibliotecarios")
        self.geometry("1240x720")
        self.minsize(1000, 600)
        ttk.Style(self).theme_use("clam")
        self._ruta = ruta
        self._crear_menu()

        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill="both", expand=True)
        self.pantallas = []
        for titulo, tipo in PANTALLAS:
            pantalla = tipo(self.pestanas, servicios)
            self.pestanas.add(pantalla, text=titulo)
            self.pantallas.append(pantalla)
        self.pestanas.bind("<<NotebookTabChanged>>", lambda _: self.refrescar_actual())

    def _crear_menu(self) -> None:
        menu = tk.Menu(self)
        archivo = tk.Menu(menu, tearoff=False)
        archivo.add_command(label="Cargar datos de ejemplo", command=self.cargar_ejemplo)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.destroy)
        menu.add_cascade(label="Archivo", menu=archivo)
        self.config(menu=menu)

    def refrescar_actual(self) -> None:
        self.nametowidget(self.pestanas.select()).refrescar()

    def cargar_ejemplo(self) -> None:
        if CargaEjemplo(self._ruta).ejecutar():
            self.refrescar_actual()
            messagebox.showinfo("Datos de ejemplo", "Datos cargados correctamente", parent=self)
        else:
            messagebox.showwarning("Datos de ejemplo", "La base ya contiene datos", parent=self)
