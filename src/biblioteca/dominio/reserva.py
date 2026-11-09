from dataclasses import dataclass
from datetime import date, timedelta

from biblioteca.config import DIAS_RETIRO_RESERVA
from biblioteca.dominio.ejemplar import Ejemplar
from biblioteca.dominio.entidad import Entidad
from biblioteca.dominio.enums import EstadoReserva
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.libro import Libro
from biblioteca.dominio.sede import Sede
from biblioteca.dominio.socio import Socio


@dataclass(kw_only=True, eq=False)
class Reserva(Entidad):
    socio: Socio
    libro: Libro
    sede: Sede
    fecha: date
    fecha_vencimiento: date | None = None
    estado: EstadoReserva = EstadoReserva.PENDIENTE
    ejemplar: Ejemplar | None = None

    def activar(self, ejemplar: Ejemplar, hoy: date) -> None:
        self._exigir(EstadoReserva.PENDIENTE, "activar")
        ejemplar.reservar()
        self.ejemplar = ejemplar
        self.fecha_vencimiento = hoy + timedelta(days=DIAS_RETIRO_RESERVA)
        self.estado = EstadoReserva.ACTIVA

    def atender(self) -> None:
        self._exigir(EstadoReserva.ACTIVA, "atender")
        self.estado = EstadoReserva.ATENDIDA

    def cancelar(self) -> None:
        if self.estado not in (EstadoReserva.PENDIENTE, EstadoReserva.ACTIVA):
            raise ReglaIncumplida(f"No se puede cancelar una reserva {self.estado}")
        self._soltar_ejemplar()
        self.estado = EstadoReserva.CANCELADA

    def vencer(self) -> None:
        self._exigir(EstadoReserva.ACTIVA, "vencer")
        self._soltar_ejemplar()
        self.estado = EstadoReserva.VENCIDA

    def esta_vencida(self, hoy: date) -> bool:
        return self.estado is EstadoReserva.ACTIVA and hoy > self.fecha_vencimiento

    def _soltar_ejemplar(self) -> None:
        if self.ejemplar is not None:
            self.ejemplar.liberar()

    def _exigir(self, estado: EstadoReserva, operacion: str) -> None:
        if self.estado is not estado:
            raise ReglaIncumplida(
                f"No se puede {operacion} una reserva en estado {self.estado}"
            )
