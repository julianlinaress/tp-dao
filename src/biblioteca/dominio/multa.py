from dataclasses import dataclass

from biblioteca.dominio.entidad import Entidad
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.estrategias_multa import EstrategiaMulta


@dataclass(kw_only=True, eq=False)
class Multa(Entidad):
    dias_atraso: int
    monto: float = 0.0
    es_pagada: bool = False

    def pagar(self) -> None:
        if self.es_pagada:
            raise ReglaIncumplida("La multa ya fue pagada")
        self.es_pagada = True

    def calcular(self, dias: int, estrategia: EstrategiaMulta) -> float:
        self.dias_atraso = dias
        self.monto = estrategia.calcular(dias)
        return self.monto
