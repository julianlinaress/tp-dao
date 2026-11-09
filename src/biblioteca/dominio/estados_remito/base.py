"""Patrón State: contrato del ciclo de vida del remito."""

from abc import ABC
from typing import ClassVar

from biblioteca.dominio.errores import TransicionInvalida

GENERADO = "Generado"
EMPAQUETADO = "Empaquetado"
EN_TRANSITO = "EnTransito"
RECIBIDO = "Recibido"
CANCELADO = "Cancelado"
CON_INCIDENCIA = "ConIncidencia"
ESTADOS_ACTIVOS = (GENERADO, EMPAQUETADO, EN_TRANSITO)


class EstadoRemito(ABC):
    nombre: ClassVar[str]
    descripcion: ClassVar[str]
    _registro: ClassVar[dict[str, type["EstadoRemito"]]] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        EstadoRemito._registro[cls.nombre] = cls

    @classmethod
    def desde_nombre(cls, nombre: str) -> "EstadoRemito":
        return cls._registro[nombre]()

    def _rechazar(self, operacion: str) -> None:
        raise TransicionInvalida(
            f"No se puede {operacion} un remito en estado {self.nombre}"
        )

    def empaquetar(self, remito, momento) -> None:
        self._rechazar("empaquetar")

    def despachar(self, remito, momento) -> None:
        self._rechazar("despachar")

    def recibir(self, remito, recepciones, momento) -> None:
        self._rechazar("recibir")

    def cancelar(self, remito, momento) -> None:
        self._rechazar("cancelar")
