"""Patrón State: contrato del ciclo de circulación del ejemplar."""

from abc import ABC
from typing import ClassVar

from biblioteca.dominio.errores import TransicionInvalida

DISPONIBLE = "Disponible"
RESERVADO = "Reservado"
PRESTADO = "Prestado"
EN_TRANSITO = "EnTransito"
PENDIENTE_RETORNO = "PendienteRetorno"
FUERA_DE_SERVICIO = "FueraDeServicio"


class EstadoEjemplar(ABC):
    nombre: ClassVar[str]
    descripcion: ClassVar[str]
    _registro: ClassVar[dict[str, type["EstadoEjemplar"]]] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        EstadoEjemplar._registro[cls.nombre] = cls

    @classmethod
    def desde_nombre(cls, nombre: str) -> "EstadoEjemplar":
        return cls._registro[nombre]()

    def _rechazar(self, operacion: str) -> None:
        raise TransicionInvalida(
            f"No se puede {operacion} un ejemplar en estado {self.nombre}"
        )

    def _sacar(self, ejemplar) -> None:
        ejemplar.cambiar_estado(FUERA_DE_SERVICIO)

    def _enviar(self, ejemplar) -> None:
        ejemplar.ubicacion_actual = None
        ejemplar.cambiar_estado(EN_TRANSITO)

    def prestar(self, ejemplar) -> None:
        self._rechazar("prestar")

    def devolver(self, ejemplar, estado_fisico) -> None:
        self._rechazar("devolver")

    def reservar(self, ejemplar) -> None:
        self._rechazar("reservar")

    def liberar(self, ejemplar) -> None:
        self._rechazar("liberar")

    def enviar(self, ejemplar) -> None:
        self._rechazar("enviar")

    def recibir(self, ejemplar, sede, apartado: bool) -> None:
        self._rechazar("recibir")

    def sacar_de_servicio(self, ejemplar) -> None:
        self._rechazar("sacar de servicio")

    def reparar(self, ejemplar) -> None:
        self._rechazar("reparar")
