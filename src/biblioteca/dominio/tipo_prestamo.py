from dataclasses import dataclass

from biblioteca.config import (
    DIAS_PRESTAMO_INTERBIBLIOTECARIO,
    DIAS_PRESTAMO_LOCAL,
    MONTO_MULTA_POR_DIA,
    TOPE_MULTA,
)
from biblioteca.dominio.estrategias_multa import (
    EstrategiaMulta,
    MultaFijaPorDia,
    MultaPorDiaConTope,
)


@dataclass(frozen=True)
class TipoPrestamo:
    nombre: str
    descripcion: str
    dias_plazo: int
    requiere_remito: bool
    estrategia_multa: EstrategiaMulta


LOCAL = TipoPrestamo(
    "Local", "Se retira y devuelve en la misma sede", DIAS_PRESTAMO_LOCAL, False,
    MultaFijaPorDia(MONTO_MULTA_POR_DIA),
)
INTERBIBLIOTECARIO = TipoPrestamo(
    "Interbibliotecario",
    "Se envía desde la sede que lo posee a la sede de retiro",
    DIAS_PRESTAMO_INTERBIBLIOTECARIO,
    True,
    MultaPorDiaConTope(MONTO_MULTA_POR_DIA, TOPE_MULTA),
)
TIPOS_PRESTAMO = {tipo.nombre: tipo for tipo in (LOCAL, INTERBIBLIOTECARIO)}
