from biblioteca.dominio.estados_ejemplar.base import PRESTADO, RESERVADO, EstadoEjemplar


class Reservado(EstadoEjemplar):
    nombre = RESERVADO
    descripcion = "Apartado para un socio"

    def prestar(self, ejemplar) -> None:
        ejemplar.cambiar_estado(PRESTADO)

    def liberar(self, ejemplar) -> None:
        ejemplar.quedar_libre()

    def enviar(self, ejemplar) -> None:
        self._enviar(ejemplar)

    def sacar_de_servicio(self, ejemplar) -> None:
        self._sacar(ejemplar)
