from dataclasses import dataclass
from datetime import date

from biblioteca.config import MAX_PRESTAMOS_ACTIVOS
from biblioteca.dominio.entidad import Entidad


@dataclass(kw_only=True, eq=False)
class Socio(Entidad):
    dni: str
    nombre: str
    apellido: str
    email: str
    fecha_alta: date
    es_habilitado: bool = True

    def habilitar(self) -> None:
        self.es_habilitado = True

    def deshabilitar(self) -> None:
        self.es_habilitado = False

    def puede_pedir_prestamo(self, prestamos_activos: int) -> bool:
        return self.es_habilitado and prestamos_activos < MAX_PRESTAMOS_ACTIVOS

    def __str__(self) -> str:
        return f"{self.apellido}, {self.nombre} ({self.dni})"
