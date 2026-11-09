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
from biblioteca.ui.tema import aplicar_tema

SECCIONES = [
    ("Circulación", [
        ("Préstamos", "Solicitudes, retiros y devoluciones", PantallaPrestamos),
        ("Envíos", "Remitos entre sedes y su recorrido", PantallaLogistica),
        ("Reservas", "Libros apartados a la espera de retiro", PantallaReservas),
        ("Multas", "Atrasos registrados y pagos", PantallaMultas),
    ]),
    ("Catálogo", [
        ("Disponibilidad", "Ejemplares libres por libro y por sede", PantallaDisponibilidad),
        ("Libros", "Fichas bibliográficas de la red", PantallaLibros),
        ("Ejemplares", "Copias físicas, ubicación y estado", PantallaEjemplares),
    ]),
    ("Red", [
        ("Socios", "Altas, datos y habilitación", PantallaSocios),
        ("Sedes", "Bibliotecas, contacto y horarios", PantallaSedes),
        ("Reportes", "Demanda, disponibilidad y movimiento", PantallaReportes),
    ]),
]


class Aplicacion(tk.Tk):
    def __init__(self, servicios, ruta: Path) -> None:
        super().__init__()
        self.title("Red de bibliotecas")
        self.geometry("1320x760")
        self.minsize(1080, 620)
        aplicar_tema(self)
        self._ruta = ruta
        self.pantallas = []
        self._botones = []
        self._textos = []
        self._actual = None

        contenido = ttk.Frame(self, padding=(26, 20))
        lateral = ttk.Frame(self, style="Nav.TFrame", padding=(0, 20, 0, 12))
        lateral.pack(side="left", fill="y")
        contenido.pack(side="left", fill="both", expand=True)

        self._titulo = ttk.Label(contenido, style="Pagina.TLabel")
        self._titulo.pack(anchor="w")
        self._subtitulo = ttk.Label(contenido, style="Subtitulo.TLabel")
        self._subtitulo.pack(anchor="w", pady=(0, 14))
        self._paginas = ttk.Frame(contenido)
        self._paginas.pack(fill="both", expand=True)

        ttk.Label(lateral, text="Red de bibliotecas", style="Marca.TLabel").pack(anchor="w", padx=18, pady=(0, 10))
        for seccion, paginas in SECCIONES:
            ttk.Label(lateral, text=seccion, style="NavSeccion.TLabel").pack(anchor="w", padx=18, pady=(14, 3))
            for titulo, subtitulo, tipo in paginas:
                self._agregar(lateral, titulo, subtitulo, tipo, servicios)
        ttk.Button(lateral, text="Cargar datos de ejemplo", style="Nav.TButton", command=self.cargar_ejemplo).pack(
            side="bottom", fill="x", padx=(8, 0)
        )
        self.mostrar(0)

    def _agregar(self, lateral, titulo, subtitulo, tipo, servicios) -> None:
        indice = len(self.pantallas)
        boton = ttk.Button(lateral, text=titulo, style="Nav.TButton", width=24, command=lambda: self.mostrar(indice))
        boton.pack(fill="x", padx=(8, 0), pady=1)
        self._botones.append(boton)
        self._textos.append((titulo, subtitulo))
        self.pantallas.append(tipo(self._paginas, servicios))

    def mostrar(self, indice: int) -> None:
        if self._actual is not None:
            self.pantallas[self._actual].pack_forget()
            self._botones[self._actual].configure(style="Nav.TButton")
        self._actual = indice
        self._botones[indice].configure(style="NavActiva.TButton")
        self._titulo.configure(text=self._textos[indice][0])
        self._subtitulo.configure(text=self._textos[indice][1])
        self.pantallas[indice].pack(fill="both", expand=True)
        self.refrescar_actual()

    def refrescar_actual(self) -> None:
        self.pantallas[self._actual].refrescar()

    def cargar_ejemplo(self) -> None:
        if CargaEjemplo(self._ruta).ejecutar():
            self.refrescar_actual()
            messagebox.showinfo("Datos de ejemplo", "Datos cargados correctamente", parent=self)
        else:
            messagebox.showwarning("Datos de ejemplo", "La base ya contiene datos", parent=self)
