from tkinter import ttk

from biblioteca.dominio.enums import EstadoFisico, EstadoPrestamo
from biblioteca.ui.componentes import Campo, Dialogo, Pantalla, Selector, Tabla, accion

COLUMNAS = [("N°", 45), ("Socio", 190), ("Libro", 200), ("Ejemplar", 85), ("Tipo", 120), ("Origen", 140), ("Destino", 140), ("Solicitud", 90), ("Vencimiento", 90), ("Estado", 90)]


class PantallaPrestamos(Pantalla):
    def construir(self) -> None:
        barra = self.barra([("Nueva solicitud", self.nueva), ("Registrar retiro", self.retirar), ("Registrar devolución", self.devolver), ("Cancelar", self.cancelar)])
        self.filtro = Selector(barra, width=16)
        self.filtro.pack(side="right")
        self.filtro.cargar([(e.value, e) for e in EstadoPrestamo], vacio="Todos")
        self.filtro.bind("<<ComboboxSelected>>", lambda _: self.refrescar())
        ttk.Label(barra, text="Estado:").pack(side="right", padx=6)
        self.tabla = Tabla(self, COLUMNAS)
        self.tabla.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        estado = self.filtro.valor()
        prestamos = self.s.prestamos.listar_por_estado(estado) if estado else self.s.prestamos.listar()
        self._prestamos = {p.id: p for p in prestamos}
        hoy = self.s.reloj.hoy()
        self.tabla.cargar(
            (p.id, (p.id, str(p.socio), p.ejemplar.libro.titulo, p.ejemplar.codigo_inventario, p.tipo.nombre,
                    p.sede_origen.nombre, p.sede_destino.nombre, p.fecha_solicitud, p.fecha_vencimiento,
                    "Vencido" if p.esta_vencido(hoy) else p.estado))
            for p in prestamos
        )

    @accion
    def nueva(self) -> None:
        sedes = self.opciones_sedes()
        datos = Dialogo.pedir(self, "Nueva solicitud de préstamo", [
            Campo("socio", "Socio", opciones=self.opciones_socios()),
            Campo("libro", "Libro", opciones=self.opciones_libros()),
            Campo("origen", "Sede que posee el ejemplar", opciones=sedes),
            Campo("destino", "Sede de retiro", opciones=sedes),
        ])
        if datos:
            self.s.prestamos.solicitar(datos["socio"], datos["libro"], datos["origen"], datos["destino"])

    @accion
    def retirar(self) -> None:
        self.s.prestamos.retirar(self.tabla.elegido())

    @accion
    def cancelar(self) -> None:
        self.s.prestamos.cancelar(self.tabla.elegido())

    @accion
    def devolver(self) -> None:
        prestamo = self._prestamos[self.tabla.elegido()]
        sedes = [(str(s), s.id) for s in self.s.sedes.listar()]
        datos = Dialogo.pedir(self, "Registrar devolución", [
            Campo("sede", "Sede", prestamo.sede_destino.id, sedes),
            Campo("fisico", "Estado físico", opciones=[(e.value, e) for e in EstadoFisico]),
            Campo("observaciones", "Observaciones"),
        ])
        if datos:
            self.s.prestamos.registrar_devolucion(prestamo.id, datos["sede"], datos["fisico"], datos["observaciones"])


class PantallaMultas(Pantalla):
    def construir(self) -> None:
        self.barra([("Registrar pago", self.pagar)])
        self.tabla = Tabla(self, [("Préstamo", 80), ("Socio", 240), ("Libro", 260), ("Días de atraso", 100), ("Monto", 100), ("Situación", 100)])
        self.tabla.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        self.tabla.cargar(
            (p.multa.id, (p.id, str(p.socio), p.ejemplar.libro.titulo, p.multa.dias_atraso,
                          f"$ {p.multa.monto:,.2f}", "Pagada" if p.multa.es_pagada else "Impaga"))
            for p in self.s.prestamos.listar_con_multa()
        )

    @accion
    def pagar(self) -> None:
        self.s.prestamos.pagar_multa(self.tabla.elegido())
