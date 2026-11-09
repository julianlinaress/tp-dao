from biblioteca.dominio.enums import EstadoRecepcion
from biblioteca.dominio.estados_remito.base import (
    CON_INCIDENCIA,
    EN_TRANSITO,
    RECIBIDO,
    EstadoRemito,
)


class EnTransito(EstadoRemito):
    nombre = EN_TRANSITO
    descripcion = "Despachado y en camino"

    def recibir(self, remito, recepciones, momento) -> None:
        for detalle in remito.detalles:
            estado, observaciones = recepciones.get(
                detalle.ejemplar.id, (EstadoRecepcion.OK, "")
            )
            detalle.registrar_recepcion(estado, observaciones, remito)
        remito.cambiar_estado(
            CON_INCIDENCIA if remito.tiene_incidencias() else RECIBIDO, momento
        )
