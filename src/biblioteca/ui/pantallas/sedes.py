from biblioteca.ui.componentes import Campo, Dialogo, Pantalla, Tabla, accion, confirmar

COLUMNAS = [("Código", 70), ("Nombre", 200), ("Dirección", 220), ("Teléfono", 110), ("Email", 200), ("Horarios", 160), ("Estado", 80)]


class PantallaSedes(Pantalla):
    def construir(self) -> None:
        self.barra([("Nueva", self.nueva), ("Modificar", self.modificar), ("Dar de baja", self.dar_baja), ("Reactivar", self.reactivar)])
        self.tabla = Tabla(self, COLUMNAS)
        self.tabla.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        self._sedes = {sede.id: sede for sede in self.s.sedes.listar()}
        self.tabla.cargar(
            (s.id, (s.codigo, s.nombre, s.direccion, s.telefono, s.email, s.horarios, "Activa" if s.es_activa else "Baja"))
            for s in self._sedes.values()
        )

    @staticmethod
    def _campos(sede=None) -> list[Campo]:
        nombres = [("codigo", "Código"), ("nombre", "Nombre"), ("direccion", "Dirección"), ("telefono", "Teléfono"), ("email", "Email"), ("horarios", "Horarios")]
        return [Campo(clave, etiqueta, getattr(sede, clave) if sede else "") for clave, etiqueta in nombres]

    @accion
    def nueva(self) -> None:
        datos = Dialogo.pedir(self, "Nueva sede", self._campos())
        if datos:
            self.s.sedes.crear(**datos)

    @accion
    def modificar(self) -> None:
        sede_id = self.tabla.elegido()
        datos = Dialogo.pedir(self, "Modificar sede", self._campos(self._sedes[sede_id]))
        if datos:
            self.s.sedes.actualizar(sede_id, **datos)

    @accion
    def dar_baja(self) -> None:
        sede = self._sedes[self.tabla.elegido()]
        if confirmar(self, f"¿Dar de baja la sede {sede}?"):
            self.s.sedes.dar_baja(sede.id)

    @accion
    def reactivar(self) -> None:
        sede = self._sedes[self.tabla.elegido()]
        if confirmar(self, f"¿Reactivar la sede {sede}?"):
            self.s.sedes.reactivar(sede.id)
