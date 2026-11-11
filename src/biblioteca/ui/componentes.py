"""Controles reutilizables de la interfaz."""

import tkinter as tk
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import wraps
from tkinter import messagebox, ttk

from biblioteca.dominio.errores import ErrorNegocio, ReglaIncumplida
from biblioteca.ui import tema

ESTADOS_DE_ALERTA = {"Vencido", "Impaga", "ConIncidencia", "Inhabilitado", "Baja", "FueraDeServicio"}


def confirmar(pantalla, mensaje: str) -> bool:
    return messagebox.askyesno("Confirmar", mensaje, parent=pantalla)


def accion(metodo: Callable) -> Callable:
    """Ejecuta una acción de pantalla, muestra los rechazos y refresca los datos."""

    @wraps(metodo)
    def envoltura(self, *args, **kwargs):
        try:
            resultado = metodo(self, *args, **kwargs)
        except ErrorNegocio as error:
            messagebox.showerror("Operación rechazada", str(error), parent=self)
            return None
        self.refrescar()
        return resultado

    return envoltura


class Tabla(ttk.Frame):
    def __init__(
        self, padre, columnas: list[tuple[str, int]], multiple: bool = False,
        vacio: str = "No hay registros para mostrar",
    ) -> None:
        super().__init__(padre, style="Borde.TFrame", padding=1)
        self._arbol = ttk.Treeview(self, show="headings", selectmode="extended" if multiple else "browse")
        barra = ttk.Scrollbar(self, orient="vertical", command=self._arbol.yview)
        self._arbol.configure(yscrollcommand=barra.set)
        self._arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self._arbol.bind("<Configure>", lambda evento: self._ajustar_columnas(evento.width))
        self._arbol.tag_configure("par", background=tema.FILA_PAR)
        self._arbol.tag_configure("alerta", background=tema.ALERTA)
        self._vacio = ttk.Label(self._arbol, text=vacio, style="Vacio.TLabel")
        self.configurar_columnas(columnas)
        self._mostrar_vacio(True)

    def configurar_columnas(self, columnas: list[tuple[str, int]]) -> None:
        self._columnas = columnas
        self._arbol["columns"] = [titulo for titulo, _ in columnas]
        for titulo, ancho in columnas:
            self._arbol.heading(titulo, text=titulo, anchor="w")
            self._arbol.column(titulo, width=ancho, anchor="w", stretch=False)
        self._ajustar_columnas(self._arbol.winfo_width())

    def _ajustar_columnas(self, ancho_total: int) -> None:
        """Reparte el ancho disponible respetando la proporción de cada columna."""
        if ancho_total <= 1:
            return
        suma = sum(ancho for _, ancho in self._columnas)
        for titulo, ancho in self._columnas:
            self._arbol.column(titulo, width=ancho_total * ancho // suma)

    def cargar(self, filas: Iterable[tuple[int, tuple]]) -> None:
        self._arbol.delete(*self._arbol.get_children())
        cantidad = 0
        for cantidad, (identificador, valores) in enumerate(filas, 1):
            textos = [self._texto(v) for v in valores]
            etiqueta = "alerta" if ESTADOS_DE_ALERTA & set(textos) else "par" if cantidad % 2 == 0 else ""
            self._arbol.insert("", "end", iid=str(identificador), values=textos, tags=(etiqueta,))
        self._mostrar_vacio(cantidad == 0)

    def _mostrar_vacio(self, visible: bool) -> None:
        if visible:
            self._vacio.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self._vacio.place_forget()

    @staticmethod
    def _texto(valor) -> str:
        return "-" if valor is None else str(valor)

    def seleccion(self) -> list[int]:
        return [int(iid) for iid in self._arbol.selection()]

    def seleccionar(self, identificadores: Iterable[int]) -> None:
        self._arbol.selection_set([str(i) for i in identificadores])

    def elegido(self) -> int:
        elegidos = self.seleccion()
        if not elegidos:
            raise ReglaIncumplida("Seleccione un registro de la tabla")
        return elegidos[0]

    def filas(self) -> list[tuple]:
        return [self._arbol.item(iid, "values") for iid in self._arbol.get_children()]


class Selector(ttk.Combobox):
    """Combo de solo lectura que devuelve el objeto elegido."""

    def __init__(self, padre, **opciones) -> None:
        super().__init__(padre, state="readonly", **opciones)
        self._valores: list = []

    def cargar(self, opciones: list[tuple[str, object]], vacio: str | None = None) -> None:
        previo = self.valor() if self.current() >= 0 else None
        pares = [(vacio, None)] + opciones if vacio is not None else opciones
        self._valores = [valor for _, valor in pares]
        self["values"] = [texto for texto, _ in pares]
        if previo in self._valores:
            self.current(self._valores.index(previo))
        elif pares:
            self.current(0)

    def valor(self):
        indice = self.current()
        return self._valores[indice] if indice >= 0 else None


@dataclass
class Campo:
    clave: str
    etiqueta: str
    inicial: object = ""
    opciones: list[tuple[str, object]] | None = None


class Dialogo(tk.Toplevel):
    """Formulario modal; `resultado` queda en None si se cancela."""

    def __init__(self, padre, titulo: str, campos: list[Campo]) -> None:
        super().__init__(padre)
        self.title(titulo)
        self.transient(padre.winfo_toplevel())
        self.configure(background=tema.FONDO)
        self.resultado: dict | None = None
        self._controles: dict[str, object] = {}

        cuerpo = ttk.Frame(self, padding=22)
        cuerpo.pack(fill="both", expand=True)
        ttk.Label(cuerpo, text=titulo, style="Pagina.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        for fila, campo in enumerate(campos, 1):
            ttk.Label(cuerpo, text=campo.etiqueta).grid(row=fila, column=0, sticky="w", pady=4, padx=(0, 16))
            control = self._crear_control(cuerpo, campo)
            control.grid(row=fila, column=1, sticky="ew", pady=4)
            self._controles[campo.clave] = control
        cuerpo.columnconfigure(1, weight=1)

        botones = ttk.Frame(cuerpo)
        botones.grid(row=len(campos) + 1, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(botones, text="Aceptar", style="Primario.TButton", command=self._aceptar).pack(side="right")
        self.bind("<Escape>", lambda _: self.destroy())

    @staticmethod
    def _crear_control(padre, campo: Campo):
        if campo.opciones is not None:
            control = Selector(padre, width=48)
            control.cargar(campo.opciones)
            valores = [valor for _, valor in campo.opciones]
            if campo.inicial in valores:
                control.current(valores.index(campo.inicial))
            return control
        control = ttk.Entry(padre, width=50)
        control.insert(0, str(campo.inicial))
        return control

    def _aceptar(self) -> None:
        self.resultado = {
            clave: control.valor() if isinstance(control, Selector) else control.get()
            for clave, control in self._controles.items()
        }
        self.destroy()

    @classmethod
    def pedir(cls, padre, titulo: str, campos: list[Campo]) -> dict | None:
        dialogo = cls(padre, titulo, campos)
        dialogo.grab_set()
        dialogo.wait_window()
        return dialogo.resultado


def mostrar_texto(padre, titulo: str, contenido: str) -> None:
    ventana = tk.Toplevel(padre)
    ventana.title(titulo)
    ventana.transient(padre.winfo_toplevel())
    texto = tk.Text(
        ventana, width=90, height=24, wrap="word", padx=20, pady=18, relief="flat", font="TkDefaultFont",
        background=tema.SUPERFICIE, foreground=tema.TINTA, selectbackground=tema.SELECCION, spacing3=4,
    )
    texto.insert("1.0", contenido)
    texto.configure(state="disabled")
    texto.pack(fill="both", expand=True)


class Pantalla(ttk.Frame):
    def __init__(self, padre, servicios) -> None:
        super().__init__(padre)
        self.s = servicios
        self.construir()

    def construir(self) -> None:
        raise NotImplementedError

    def refrescar(self) -> None:
        raise NotImplementedError

    def barra(self, acciones: list[tuple[str, Callable]], padre=None) -> ttk.Frame:
        marco = ttk.Frame(padre or self)
        marco.pack(fill="x", pady=(0, 10))
        for orden, (texto, comando) in enumerate(acciones):
            estilo = "Primario.TButton" if orden == 0 else "TButton"
            ttk.Button(marco, text=texto, style=estilo, command=comando).pack(side="left", padx=(0, 6))
        return marco

    def opciones_sedes(self) -> list[tuple[str, int]]:
        return [(str(sede), sede.id) for sede in self.s.sedes.listar_activas()]

    def opciones_libros(self) -> list[tuple[str, int]]:
        return [(str(libro), libro.id) for libro in self.s.catalogo.listar_libros()]

    def opciones_socios(self) -> list[tuple[str, int]]:
        return [(str(socio), socio.id) for socio in self.s.socios.listar()]
