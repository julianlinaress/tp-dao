"""Gestión de reservas y su vencimiento automático."""

from biblioteca.dominio.ejemplar import Ejemplar
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.prestamo import SolicitudPrestamo
from biblioteca.dominio.reserva import Reserva
from biblioteca.dominio.tipo_prestamo import LOCAL
from biblioteca.servicios.validaciones import exigir_sede_activa, exigir_socio_habilitado


class ReservaServicio:
    def __init__(self, repositorios, reloj) -> None:
        self._r = repositorios
        self._reloj = reloj

    def crear(self, socio_id: int, libro_id: int, sede_id: int) -> Reserva:
        with self._r.transaccion():
            socio = self._r.socios.requerir(socio_id)
            libro = self._r.libros.requerir(libro_id)
            sede = self._r.sedes.requerir(sede_id)
            exigir_socio_habilitado(socio)
            exigir_sede_activa(sede)

            ejemplares = self._r.ejemplares.listar_por_libro_y_sede(libro_id, sede_id)
            if not ejemplares:
                raise ReglaIncumplida("La sede no posee ejemplares de ese libro")
            if any(ejemplar.puede_entregarse() for ejemplar in ejemplares):
                raise ReglaIncumplida("Hay ejemplares disponibles: solicite un préstamo")

            reserva = Reserva(socio=socio, libro=libro, sede=sede, fecha=self._reloj.hoy())
            return self._r.reservas.crear(reserva)

    def atender_liberado(self, ejemplar: Ejemplar) -> Reserva | None:
        """Aparta un ejemplar que quedó libre para la reserva pendiente más antigua."""
        if not ejemplar.puede_entregarse():
            return None
        with self._r.transaccion():
            reserva = self._r.reservas.siguiente_pendiente(ejemplar.libro.id, ejemplar.sede.id)
            if reserva is None:
                return None
            reserva.activar(ejemplar, self._reloj.hoy())
            self._r.ejemplares.actualizar(ejemplar)
            self._r.reservas.actualizar(reserva)
            return reserva

    def retirar(self, reserva_id: int) -> SolicitudPrestamo:
        hoy = self._reloj.hoy()
        with self._r.transaccion():
            reserva = self._r.reservas.requerir(reserva_id)
            if reserva.esta_vencida(hoy):
                raise ReglaIncumplida("La reserva está vencida")
            exigir_sede_activa(reserva.sede)
            exigir_socio_habilitado(reserva.socio)
            if self._r.prestamos.tiene_vencidos(reserva.socio.id, hoy):
                raise ReglaIncumplida("El socio tiene préstamos vencidos")
            vigentes = self._r.prestamos.contar_vigentes(reserva.socio.id)
            if not reserva.socio.puede_pedir_prestamo(vigentes):
                raise ReglaIncumplida("El socio alcanzó el máximo de préstamos activos")
            reserva.atender()
            prestamo = SolicitudPrestamo(
                socio=reserva.socio, ejemplar=reserva.ejemplar, sede_origen=reserva.sede,
                sede_destino=reserva.sede, tipo=LOCAL, fecha_solicitud=hoy,
            )
            prestamo.retirar(hoy)
            self._r.prestamos.crear(prestamo)
            self._r.ejemplares.actualizar(reserva.ejemplar)
            self._r.reservas.actualizar(reserva)
            return prestamo

    def cancelar(self, reserva_id: int) -> None:
        with self._r.transaccion():
            reserva = self._r.reservas.requerir(reserva_id)
            reserva.cancelar()
            self._cerrar_y_reasignar(reserva)

    def vencer_vencidas(self) -> int:
        hoy = self._reloj.hoy()
        with self._r.transaccion():
            vencidas = [r for r in self._r.reservas.listar_activas() if r.esta_vencida(hoy)]
            for reserva in vencidas:
                reserva.vencer()
                self._cerrar_y_reasignar(reserva)
            return len(vencidas)

    def listar(self) -> list[Reserva]:
        return self._r.reservas.listar()

    def _cerrar_y_reasignar(self, reserva: Reserva) -> None:
        self._r.reservas.actualizar(reserva)
        if reserva.ejemplar is not None:
            self._r.ejemplares.actualizar(reserva.ejemplar)
            self.atender_liberado(reserva.ejemplar)
