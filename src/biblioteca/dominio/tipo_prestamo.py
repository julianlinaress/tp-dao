from dataclasses import dataclass

from biblioteca.config import DIAS_PRESTAMO_INTERBIBLIOTECARIO, DIAS_PRESTAMO_LOCAL


@dataclass(frozen=True)
class TipoPrestamo:
    nombre: str
    descripcion: str
    dias_plazo: int
    requiere_remito: bool


LOCAL = TipoPrestamo(
    "Local", "Se retira y devuelve en la misma sede", DIAS_PRESTAMO_LOCAL, False
)
INTERBIBLIOTECARIO = TipoPrestamo(
    "Interbibliotecario",
    "Se envía desde la sede que lo posee a la sede de retiro",
    DIAS_PRESTAMO_INTERBIBLIOTECARIO,
    True,
)
TIPOS_PRESTAMO = {tipo.nombre: tipo for tipo in (LOCAL, INTERBIBLIOTECARIO)}
