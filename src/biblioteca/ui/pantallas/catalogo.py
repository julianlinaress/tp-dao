from tkinter import ttk

from biblioteca.dominio.enums import EstadoFisico
from biblioteca.ui.componentes import Campo, Dialogo, Pantalla, Selector, Tabla, accion, confirmar

ESTADOS_FISICOS = [(estado.value, estado) for estado in EstadoFisico]


class PantallaLibros(Pantalla):
    def construir(self) -> None:
        self.barra([("Nuevo", self.nuevo), ("Modificar", self.modificar), ("Eliminar", self.eliminar)])
        self.tabla = Tabla(self, [("ISBN", 130), ("Título", 260), ("Autor", 200), ("Edición", 80), ("Género", 120), ("Editorial", 160)])
        self.tabla.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        self._libros = {libro.id: libro for libro in self.s.catalogo.listar_libros()}
        self.tabla.cargar((x.id, (x.isbn, x.titulo, x.autor, x.edicion, x.genero, x.editorial)) for x in self._libros.values())

    @staticmethod
    def _campos(libro=None) -> list[Campo]:
        nombres = [("isbn", "ISBN"), ("titulo", "Título"), ("autor", "Autor"), ("edicion", "Edición"), ("genero", "Género"), ("editorial", "Editorial")]
        return [Campo(clave, etiqueta, getattr(libro, clave) if libro else "") for clave, etiqueta in nombres]

    @accion
    def nuevo(self) -> None:
        datos = Dialogo.pedir(self, "Nuevo libro", self._campos())
        if datos:
            self.s.catalogo.crear_libro(**datos)

    @accion
    def modificar(self) -> None:
        libro_id = self.tabla.elegido()
        datos = Dialogo.pedir(self, "Modificar libro", self._campos(self._libros[libro_id]))
        if datos:
            self.s.catalogo.actualizar_libro(libro_id, **datos)

    @accion
    def eliminar(self) -> None:
        libro = self._libros[self.tabla.elegido()]
        if confirmar(self, f"¿Eliminar el libro «{libro.titulo}»?"):
            self.s.catalogo.eliminar_libro(libro.id)


class PantallaEjemplares(Pantalla):
    def construir(self) -> None:
        self.barra([("Nuevo", self.nuevo), ("Sacar de servicio", self.sacar), ("Reparar / Reincorporar", self.reparar), ("Eliminar", self.eliminar)])
        self.tabla = Tabla(self, [("Inventario", 100), ("Libro", 280), ("Sede", 180), ("Ubicación actual", 180), ("Circulación", 130), ("Estado físico", 110)])
        self.tabla.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        self.tabla.cargar(
            (e.id, (e.codigo_inventario, e.libro.titulo, e.sede.nombre,
                    e.ubicacion_actual.nombre if e.ubicacion_actual else None,
                    e.estado_circulacion.nombre, e.estado_fisico))
            for e in self.s.catalogo.listar_ejemplares()
        )

    @accion
    def eliminar(self) -> None:
        ejemplar_id = self.tabla.elegido()
        if confirmar(self, "¿Eliminar el ejemplar seleccionado?"):
            self.s.catalogo.eliminar_ejemplar(ejemplar_id)

    @accion
    def nuevo(self) -> None:
        datos = Dialogo.pedir(self, "Nuevo ejemplar", [
            Campo("libro", "Libro", opciones=self.opciones_libros()),
            Campo("sede", "Sede", opciones=self.opciones_sedes()),
            Campo("codigo", "Código de inventario"),
            Campo("fisico", "Estado físico", opciones=ESTADOS_FISICOS),
        ])
        if datos:
            self.s.catalogo.crear_ejemplar(datos["libro"], datos["sede"], datos["codigo"], datos["fisico"])

    @accion
    def sacar(self) -> None:
        ejemplar_id = self.tabla.elegido()
        datos = Dialogo.pedir(self, "Sacar de servicio", [Campo("fisico", "Estado físico", EstadoFisico.DANADO, ESTADOS_FISICOS)])
        if datos:
            self.s.catalogo.sacar_de_servicio(ejemplar_id, datos["fisico"])

    @accion
    def reparar(self) -> None:
        ejemplar_id = self.tabla.elegido()
        if confirmar(self, "¿Reparar / reincorporar el ejemplar seleccionado?"):
            self.s.catalogo.reparar(ejemplar_id)


class PantallaDisponibilidad(Pantalla):
    def construir(self) -> None:
        marco = ttk.Frame(self)
        marco.pack(fill="x", pady=(0, 8))
        ttk.Label(marco, text="Libro:").pack(side="left")
        self.libro = Selector(marco, width=40)
        self.libro.pack(side="left", padx=6)
        ttk.Label(marco, text="Sede:").pack(side="left")
        self.sede = Selector(marco, width=28)
        self.sede.pack(side="left", padx=6)
        for selector in (self.libro, self.sede):
            selector.bind("<<ComboboxSelected>>", lambda _: self.refrescar())
        self.tabla = Tabla(self, [("Libro", 320), ("Sede", 220), ("Ejemplares", 100), ("Disponibles", 100)])
        self.tabla.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        self.libro.cargar(self.opciones_libros(), vacio="Todos")
        self.sede.cargar([(str(s), s.id) for s in self.s.sedes.listar()], vacio="Todas")
        filas = self.s.catalogo.disponibilidad(self.libro.valor(), self.sede.valor())
        self.tabla.cargar((i, (f["titulo"], f["sede"], f["total"], f["disponibles"])) for i, f in enumerate(filas))
