from biblioteca.dominio.estados_ejemplar.base import (
    DISPONIBLE,
    PRESTADO,
    RESERVADO,
    EstadoEjemplar,
)


class Disponible(EstadoEjemplar):
    nombre = DISPONIBLE
    descripcion = "En su sede y listo para prestar o reservar"

    def prestar(self, ejemplar) -> None:
        ejemplar.cambiar_estado(PRESTADO)

    def reservar(self, ejemplar) -> None:
        ejemplar.cambiar_estado(RESERVADO)

    def enviar(self, ejemplar) -> None:
        self._enviar(ejemplar)

    def sacar_de_servicio(self, ejemplar) -> None:
        self._sacar(ejemplar)
