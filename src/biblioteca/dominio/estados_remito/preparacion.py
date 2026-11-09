"""Estados previos al despacho, los únicos que admiten cancelación."""

from biblioteca.dominio.estados_remito.base import (
    CANCELADO,
    EMPAQUETADO,
    EN_TRANSITO,
    GENERADO,
    EstadoRemito,
)


class Generado(EstadoRemito):
    nombre = GENERADO
    descripcion = "Creado, con los ejemplares aún sin empaquetar"

    def empaquetar(self, remito, momento) -> None:
        remito.cambiar_estado(EMPAQUETADO, momento)

    def cancelar(self, remito, momento) -> None:
        remito.cambiar_estado(CANCELADO, momento)


class Empaquetado(EstadoRemito):
    nombre = EMPAQUETADO
    descripcion = "Ejemplares listos para el envío"

    def despachar(self, remito, momento) -> None:
        for detalle in remito.detalles:
            detalle.ejemplar.enviar()
        remito.cambiar_estado(EN_TRANSITO, momento)

    def cancelar(self, remito, momento) -> None:
        remito.cambiar_estado(CANCELADO, momento)
