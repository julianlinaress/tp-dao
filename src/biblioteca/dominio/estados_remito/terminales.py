"""Estados finales: heredan el rechazo de todas las operaciones."""

from biblioteca.dominio.estados_remito.base import (
    CANCELADO,
    CON_INCIDENCIA,
    RECIBIDO,
    EstadoRemito,
)


class Recibido(EstadoRemito):
    nombre = RECIBIDO
    descripcion = "Llegó a destino sin novedades"


class Cancelado(EstadoRemito):
    nombre = CANCELADO
    descripcion = "Anulado antes del despacho"


class ConIncidencia(EstadoRemito):
    nombre = CON_INCIDENCIA
    descripcion = "Recibido con al menos un ejemplar dañado, destruido o extraviado"
