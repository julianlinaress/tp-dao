from dataclasses import dataclass
from datetime import datetime

from biblioteca.dominio.entidad import Entidad


@dataclass(kw_only=True, eq=False)
class CambioEstado(Entidad):
    estado_anterior: str
    estado_nuevo: str
    fecha_hora_inicio: datetime
    fecha_hora_fin: datetime
