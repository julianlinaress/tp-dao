from tkinter import ttk

from biblioteca.ui.componentes import Campo, Dialogo, Pantalla, Tabla, accion

COLUMNAS = [("DNI", 100), ("Apellido", 170), ("Nombre", 170), ("Email", 240), ("Alta", 100), ("Situación", 110)]


class PantallaSocios(Pantalla):
    def construir(self) -> None:
        barra = self.barra([("Nuevo", self.nuevo), ("Modificar", self.modificar), ("Habilitar / Inhabilitar", self.alternar)])
        self.busqueda = ttk.Entry(barra, width=28)
        self.busqueda.pack(side="right")
        self.busqueda.bind("<KeyRelease>", lambda _: self.refrescar())
        ttk.Label(barra, text="Buscar:").pack(side="right", padx=6)
        self.tabla = Tabla(self, COLUMNAS)
        self.tabla.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        self._socios = {socio.id: socio for socio in self.s.socios.listar(self.busqueda.get())}
        self.tabla.cargar(
            (s.id, (s.dni, s.apellido, s.nombre, s.email, s.fecha_alta, "Habilitado" if s.es_habilitado else "Inhabilitado"))
            for s in self._socios.values()
        )

    @staticmethod
    def _campos(socio=None) -> list[Campo]:
        nombres = [("dni", "DNI"), ("nombre", "Nombre"), ("apellido", "Apellido"), ("email", "Email")]
        return [Campo(clave, etiqueta, getattr(socio, clave) if socio else "") for clave, etiqueta in nombres]

    @accion
    def nuevo(self) -> None:
        datos = Dialogo.pedir(self, "Nuevo socio", self._campos())
        if datos:
            self.s.socios.crear(**datos)

    @accion
    def modificar(self) -> None:
        socio_id = self.tabla.elegido()
        datos = Dialogo.pedir(self, "Modificar socio", self._campos(self._socios[socio_id]))
        if datos:
            self.s.socios.actualizar(socio_id, **datos)

    @accion
    def alternar(self) -> None:
        socio_id = self.tabla.elegido()
        self.s.socios.cambiar_habilitacion(socio_id, not self._socios[socio_id].es_habilitado)
