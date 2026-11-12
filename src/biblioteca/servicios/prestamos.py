"""Solicitudes de préstamo, retiros, devoluciones y multas."""

from biblioteca.dominio.ejemplar import Ejemplar
from biblioteca.dominio.enums import EstadoFisico, EstadoPrestamo
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.prestamo import SolicitudPrestamo
from biblioteca.dominio.tipo_prestamo import INTERBIBLIOTECARIO, LOCAL
from biblioteca.servicios.validaciones import exigir_sede_activa, exigir_socio_habilitado


class PrestamoServicio:
    def __init__(self, repositorios, reloj, reservas) -> None:
        self._r = repositorios
        self._reloj = reloj
        self._reservas = reservas

    def solicitar(
        self, socio_id: int, libro_id: int, sede_origen_id: int, sede_destino_id: int,
        ejemplar_id: int | None = None,
    ) -> SolicitudPrestamo:
        hoy = self._reloj.hoy()
        with self._r.transaccion():
            socio = self._r.socios.requerir(socio_id)
            origen = self._r.sedes.requerir(sede_origen_id)
            destino = self._r.sedes.requerir(sede_destino_id)
            exigir_sede_activa(origen)
            exigir_sede_activa(destino)
            exigir_socio_habilitado(socio)
            if self._r.prestamos.tiene_vencidos(socio.id, hoy):
                raise ReglaIncumplida("El socio tiene préstamos vencidos")
            if not socio.puede_pedir_prestamo(self._r.prestamos.contar_vigentes(socio.id)):
                raise ReglaIncumplida("El socio alcanzó el máximo de préstamos activos")

            ejemplar = self._ejemplar_apto(libro_id, origen, ejemplar_id)
            ejemplar.reservar()
            prestamo = SolicitudPrestamo(
                socio=socio, ejemplar=ejemplar, sede_origen=origen, sede_destino=destino,
                tipo=LOCAL if origen == destino else INTERBIBLIOTECARIO, fecha_solicitud=hoy,
            )
            self._r.prestamos.crear(prestamo)
            self._r.ejemplares.actualizar(ejemplar)
            return prestamo

    def _ejemplar_apto(self, libro_id, origen, ejemplar_id) -> Ejemplar:
        self._r.libros.requerir(libro_id)
        if ejemplar_id is not None:
            elegido = self._r.ejemplares.requerir(ejemplar_id)
            if elegido.sede != origen or elegido.libro.id != libro_id:
                raise ReglaIncumplida("El ejemplar no pertenece a la sede de origen del préstamo")
            if not elegido.puede_entregarse():
                raise ReglaIncumplida("El ejemplar no está disponible")
            return elegido

        aptos = [
            ejemplar
            for ejemplar in self._r.ejemplares.listar_por_libro_y_sede(libro_id, origen.id)
            if ejemplar.puede_entregarse()
        ]
        if not aptos:
            raise ReglaIncumplida("No hay ejemplares disponibles en la sede de origen")
        return min(aptos, key=lambda e: e.estado_fisico is not EstadoFisico.BUENO)

    def retirar(self, prestamo_id: int) -> SolicitudPrestamo:
        with self._r.transaccion():
            prestamo = self._r.prestamos.requerir(prestamo_id)
            exigir_socio_habilitado(prestamo.socio)
            prestamo.retirar(self._reloj.hoy())
            self._r.prestamos.actualizar(prestamo)
            self._r.ejemplares.actualizar(prestamo.ejemplar)
            return prestamo

    def cancelar(self, prestamo_id: int) -> None:
        with self._r.transaccion():
            prestamo = self._r.prestamos.requerir(prestamo_id)
            if self._r.detalles.ejemplar_en_remito_activo(prestamo.ejemplar.id):
                raise ReglaIncumplida("El ejemplar está en un remito activo: cancele el remito antes")
            prestamo.cancelar()
            self._r.prestamos.actualizar(prestamo)
            self._r.ejemplares.actualizar(prestamo.ejemplar)
            self._reservas.atender_liberado(prestamo.ejemplar)

    def registrar_devolucion(
        self, prestamo_id: int, sede_id: int, estado_fisico: EstadoFisico, observaciones: str = "",
    ) -> SolicitudPrestamo:
        with self._r.transaccion():
            prestamo = self._r.prestamos.requerir(prestamo_id)
            sede = self._r.sedes.requerir(sede_id)
            prestamo.registrar_devolucion(
                sede, self._reloj.hoy(), estado_fisico, observaciones.strip()
            )
            self._r.prestamos.actualizar(prestamo)
            self._r.ejemplares.actualizar(prestamo.ejemplar)
            self._reservas.atender_liberado(prestamo.ejemplar)
            return prestamo

    def listar(self) -> list[SolicitudPrestamo]:
        return self._r.prestamos.listar()

    def listar_por_estado(self, estado: EstadoPrestamo) -> list[SolicitudPrestamo]:
        return self._r.prestamos.listar_por_estado(estado)

    def listar_con_multa(self) -> list[SolicitudPrestamo]:
        return self._r.prestamos.listar_con_multa()

    def pagar_multa(self, multa_id: int) -> None:
        with self._r.transaccion():
            multa = self._r.multas.requerir(multa_id)
            multa.pagar()
            self._r.multas.actualizar(multa)
