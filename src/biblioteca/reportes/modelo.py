"""Estructuras comunes y plantilla de los reportes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import ClassVar


@dataclass
class FiltroReporte:
    sede_id: int | None = None
    desde: date | None = None
    hasta: date | None = None
    genero: str | None = None
    tipo_prestamo: str | None = None
    tipo_remito: str | None = None
    limite: int = 10

    def parametros(self) -> dict:
        return {
            "sede": self.sede_id,
            "desde": self.desde.isoformat() if self.desde else None,
            "hasta": self.hasta.isoformat() if self.hasta else None,
            "genero": self.genero,
            "tipo_prestamo": self.tipo_prestamo,
            "tipo_remito": self.tipo_remito,
            "limite": self.limite,
        }


@dataclass
class Grafico:
    titulo: str
    etiquetas: list[str]
    valores: list[float]


@dataclass
class ResultadoReporte:
    titulo: str
    columnas: list[str]
    filas: list[tuple]
    metricas: dict[str, str] = field(default_factory=dict)
    grafico: Grafico | None = None


class Reporte(ABC):
    """Método plantilla: cada reporte define sus datos, métricas y gráfico."""

    titulo: ClassVar[str]
    columnas: ClassVar[list[str]]
    filtros: ClassVar[set[str]]

    def __init__(self, dao, reloj) -> None:
        self._dao = dao
        self._reloj = reloj

    def generar(self, filtro: FiltroReporte) -> ResultadoReporte:
        filas = [tuple(fila) for fila in self._datos(filtro)]
        return ResultadoReporte(
            self.titulo, self.columnas, filas, self._metricas(filas), self._grafico(filas)
        )

    @abstractmethod
    def _datos(self, filtro: FiltroReporte) -> list:
        pass

    @abstractmethod
    def _metricas(self, filas: list[tuple]) -> dict[str, str]:
        pass

    @abstractmethod
    def _grafico(self, filas: list[tuple]) -> Grafico | None:
        pass


def sumar_por(filas: list[tuple], indice_clave: int, indice_valor: int | None = None) -> dict:
    """Acumula por clave; sin índice de valor cuenta filas."""
    acumulado: dict = {}
    for fila in filas:
        valor = 1 if indice_valor is None else fila[indice_valor]
        acumulado[fila[indice_clave]] = acumulado.get(fila[indice_clave], 0) + valor
    return acumulado


def grafico_desde(titulo: str, datos: dict) -> Grafico | None:
    return Grafico(titulo, list(datos), list(datos.values())) if datos else None
