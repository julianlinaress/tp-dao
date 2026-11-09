from dataclasses import dataclass

from biblioteca.dominio.ejemplar import Ejemplar
from biblioteca.dominio.entidad import Entidad
from biblioteca.dominio.enums import EstadoRecepcion
from biblioteca.dominio.prestamo import SolicitudPrestamo


@dataclass(kw_only=True, eq=False)
class DetalleRemito(Entidad):
    ejemplar: Ejemplar
    prestamo: SolicitudPrestamo
    estado_recepcion: EstadoRecepcion | None = None
    observaciones: str = ""

    def registrar_recepcion(
        self, estado: EstadoRecepcion, observaciones: str, remito
    ) -> None:
        self.estado_recepcion = estado
        self.observaciones = observaciones
        if estado is EstadoRecepcion.OK:
            self.ejemplar.recibir(remito.sede_destino, apartado=remito.es_ida())
            return
        if estado is not EstadoRecepcion.EXTRAVIADO:
            self.ejemplar.ubicacion_actual = remito.sede_destino
        self.ejemplar.sacar_de_servicio(estado.estado_fisico)
