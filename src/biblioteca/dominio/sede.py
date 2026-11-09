from dataclasses import dataclass

from biblioteca.dominio.entidad import Entidad


@dataclass(kw_only=True, eq=False)
class Sede(Entidad):
    codigo: str
    nombre: str
    direccion: str
    telefono: str
    email: str
    horarios: str
    es_activa: bool = True

    def dar_baja(self) -> None:
        self.es_activa = False

    def esta_activa(self) -> bool:
        return self.es_activa

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"
