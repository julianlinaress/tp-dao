from dataclasses import dataclass
from datetime import date, timedelta

from biblioteca.dominio.devolucion import Devolucion
from biblioteca.dominio.ejemplar import Ejemplar
from biblioteca.dominio.entidad import Entidad
from biblioteca.dominio.enums import EstadoFisico, EstadoPrestamo
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.multa import Multa
from biblioteca.dominio.sede import Sede
from biblioteca.dominio.socio import Socio
from biblioteca.dominio.tipo_prestamo import TipoPrestamo


@dataclass(kw_only=True, eq=False)
class SolicitudPrestamo(Entidad):
    socio: Socio
    ejemplar: Ejemplar
    sede_origen: Sede
    sede_destino: Sede
    tipo: TipoPrestamo
    fecha_solicitud: date
    fecha_retiro: date | None = None
    fecha_vencimiento: date | None = None
    estado: EstadoPrestamo = EstadoPrestamo.SOLICITADO
    devolucion: Devolucion | None = None
    multa: Multa | None = None

    def esta_vencido(self, hoy: date) -> bool:
        return self.estado is EstadoPrestamo.ACTIVO and hoy > self.fecha_vencimiento

    def retirar(self, fecha: date) -> None:
        self._exigir(EstadoPrestamo.SOLICITADO, "retirar")
        if self.ejemplar.ubicacion_actual != self.sede_destino:
            raise ReglaIncumplida("El ejemplar todavía no está en la sede de retiro")
        self.ejemplar.prestar()
        self.fecha_retiro = fecha
        self.fecha_vencimiento = fecha + timedelta(days=self.tipo.dias_plazo)
        self.estado = EstadoPrestamo.ACTIVO

    def cancelar(self) -> None:
        self._exigir(EstadoPrestamo.SOLICITADO, "cancelar")
        self.ejemplar.liberar()
        self.estado = EstadoPrestamo.CANCELADO

    def anular_por_incidencia(self) -> None:
        self._exigir(EstadoPrestamo.SOLICITADO, "anular")
        self.estado = EstadoPrestamo.CANCELADO

    def registrar_devolucion(
        self,
        sede: Sede,
        fecha: date,
        estado_fisico: EstadoFisico,
        observaciones: str,
    ) -> Devolucion:
        self._exigir(EstadoPrestamo.ACTIVO, "devolver")
        if sede != self.sede_destino:
            raise ReglaIncumplida("La devolución debe registrarse en la sede de retiro")
        if fecha < self.fecha_retiro:
            raise ReglaIncumplida("La devolución no puede ser anterior al retiro")

        self.ejemplar.devolver(estado_fisico)
        self.devolucion = Devolucion(
            fecha=fecha, estado_fisico=estado_fisico, sede=sede, observaciones=observaciones
        )
        self.estado = EstadoPrestamo.DEVUELTO
        dias_atraso = (fecha - self.fecha_vencimiento).days
        if dias_atraso > 0:
            self.multa = Multa(dias_atraso=dias_atraso)
            self.multa.calcular(dias_atraso, self.tipo.estrategia_multa)
        return self.devolucion

    def _exigir(self, estado: EstadoPrestamo, operacion: str) -> None:
        if self.estado is not estado:
            raise ReglaIncumplida(
                f"No se puede {operacion} un préstamo en estado {self.estado}"
            )
