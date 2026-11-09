"""Valores cerrados del dominio."""

from enum import StrEnum


class EstadoFisico(StrEnum):
    BUENO = "Bueno"
    DETERIORADO = "Deteriorado"
    DANADO = "Dañado"
    DESTRUIDO = "Destruido"

    @property
    def requiere_reparacion(self) -> bool:
        return self in (EstadoFisico.DANADO, EstadoFisico.DESTRUIDO)


class EstadoRecepcion(StrEnum):
    OK = "OK"
    DANADO = "Dañado"
    EXTRAVIADO = "Extraviado"
    DESTRUIDO = "Destruido"

    @property
    def estado_fisico(self) -> EstadoFisico | None:
        return {
            EstadoRecepcion.DANADO: EstadoFisico.DANADO,
            EstadoRecepcion.DESTRUIDO: EstadoFisico.DESTRUIDO,
        }.get(self)


class EstadoPrestamo(StrEnum):
    SOLICITADO = "Solicitado"
    ACTIVO = "Activo"
    DEVUELTO = "Devuelto"
    CANCELADO = "Cancelado"


class EstadoReserva(StrEnum):
    PENDIENTE = "Pendiente"
    ACTIVA = "Activa"
    ATENDIDA = "Atendida"
    VENCIDA = "Vencida"
    CANCELADA = "Cancelada"


class TipoRemito(StrEnum):
    IDA = "Ida"
    RETORNO = "Retorno"
