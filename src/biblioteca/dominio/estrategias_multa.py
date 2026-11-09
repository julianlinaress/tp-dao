"""Patrón Strategy: políticas intercambiables de cálculo de multas."""

from abc import ABC, abstractmethod


class EstrategiaMulta(ABC):
    @abstractmethod
    def calcular(self, dias: int) -> float:
        pass


class MultaFijaPorDia(EstrategiaMulta):
    def __init__(self, monto_por_dia: float) -> None:
        self._monto_por_dia = monto_por_dia

    def calcular(self, dias: int) -> float:
        return dias * self._monto_por_dia


class MultaPorDiaConTope(EstrategiaMulta):
    def __init__(self, monto_por_dia: float, tope: float) -> None:
        self._monto_por_dia = monto_por_dia
        self._tope = tope

    def calcular(self, dias: int) -> float:
        return min(dias * self._monto_por_dia, self._tope)
