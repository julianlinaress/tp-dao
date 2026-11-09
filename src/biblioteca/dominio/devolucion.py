from dataclasses import dataclass
from datetime import date

from biblioteca.dominio.entidad import Entidad
from biblioteca.dominio.enums import EstadoFisico
from biblioteca.dominio.sede import Sede


@dataclass(kw_only=True, eq=False)
class Devolucion(Entidad):
    fecha: date
    estado_fisico: EstadoFisico
    sede: Sede
    observaciones: str = ""

    def requiere_reparacion(self) -> bool:
        return self.estado_fisico.requiere_reparacion
