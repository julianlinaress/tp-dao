from biblioteca.dominio.estados_ejemplar.base import (
    FUERA_DE_SERVICIO,
    PRESTADO,
    EstadoEjemplar,
)


class Prestado(EstadoEjemplar):
    nombre = PRESTADO
    descripcion = "En manos de un socio"

    def devolver(self, ejemplar, estado_fisico) -> None:
        ejemplar.estado_fisico = estado_fisico
        if estado_fisico.requiere_reparacion:
            ejemplar.cambiar_estado(FUERA_DE_SERVICIO)
        else:
            ejemplar.quedar_libre()

    def sacar_de_servicio(self, ejemplar) -> None:
        self._sacar(ejemplar)
