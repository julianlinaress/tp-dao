from dataclasses import dataclass, field
from datetime import datetime

from biblioteca.dominio.cambio_estado import CambioEstado
from biblioteca.dominio.detalle_remito import DetalleRemito
from biblioteca.dominio.entidad import Entidad
from biblioteca.dominio.enums import EstadoRecepcion, TipoRemito
from biblioteca.dominio.estados_remito import ESTADOS_ACTIVOS, EstadoRemito, Generado
from biblioteca.dominio.sede import Sede


@dataclass(kw_only=True, eq=False)
class Remito(Entidad):
    tipo: TipoRemito
    fecha_emision: datetime
    sede_origen: Sede
    sede_destino: Sede
    observaciones: str = ""
    estado: EstadoRemito = field(default_factory=Generado)
    detalles: list[DetalleRemito] = field(default_factory=list)
    cambios: list[CambioEstado] = field(default_factory=list)

    def cambiar_estado(self, nombre: str, momento: datetime) -> None:
        inicio = self.cambios[-1].fecha_hora_fin if self.cambios else self.fecha_emision
        self.cambios.append(
            CambioEstado(
                estado_anterior=self.estado.nombre,
                estado_nuevo=nombre,
                fecha_hora_inicio=inicio,
                fecha_hora_fin=momento,
            )
        )
        self.estado = EstadoRemito.desde_nombre(nombre)

    def empaquetar(self, momento: datetime) -> None:
        self.estado.empaquetar(self, momento)

    def despachar(self, momento: datetime) -> None:
        self.estado.despachar(self, momento)

    def recibir(self, recepciones: dict, momento: datetime) -> None:
        """recepciones: {id de ejemplar: (EstadoRecepcion, observaciones)}; por defecto OK."""
        self.estado.recibir(self, recepciones, momento)

    def cancelar(self, momento: datetime) -> None:
        self.estado.cancelar(self, momento)

    def es_ida(self) -> bool:
        return self.tipo is TipoRemito.IDA

    def esta_activo(self) -> bool:
        return self.estado.nombre in ESTADOS_ACTIVOS

    def tiene_incidencias(self) -> bool:
        return any(
            detalle.estado_recepcion not in (None, EstadoRecepcion.OK)
            for detalle in self.detalles
        )
