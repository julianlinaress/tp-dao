from biblioteca.ui.componentes import Campo, Dialogo, Pantalla, Tabla, accion

COLUMNAS = [("N°", 50), ("Socio", 220), ("Libro", 260), ("Sede", 180), ("Fecha", 95), ("Retirar hasta", 95), ("Ejemplar", 90), ("Estado", 90)]


class PantallaReservas(Pantalla):
    def construir(self) -> None:
        self.barra([("Nueva", self.nueva), ("Registrar retiro", self.retirar), ("Cancelar", self.cancelar)])
        self.tabla = Tabla(self, COLUMNAS)
        self.tabla.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        self.s.reservas.vencer_vencidas()
        self.tabla.cargar(
            (r.id, (r.id, str(r.socio), r.libro.titulo, r.sede.nombre, r.fecha, r.fecha_vencimiento,
                    r.ejemplar.codigo_inventario if r.ejemplar else None, r.estado))
            for r in self.s.reservas.listar()
        )

    @accion
    def nueva(self) -> None:
        datos = Dialogo.pedir(self, "Nueva reserva", [
            Campo("socio", "Socio", opciones=self.opciones_socios()),
            Campo("libro", "Libro", opciones=self.opciones_libros()),
            Campo("sede", "Sede de retiro", opciones=self.opciones_sedes()),
        ])
        if datos:
            self.s.reservas.crear(datos["socio"], datos["libro"], datos["sede"])

    @accion
    def retirar(self) -> None:
        self.s.reservas.retirar(self.tabla.elegido())

    @accion
    def cancelar(self) -> None:
        self.s.reservas.cancelar(self.tabla.elegido())
