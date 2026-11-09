from biblioteca.dominio.estados_ejemplar.base import EN_TRANSITO, RESERVADO, EstadoEjemplar


class EnTransito(EstadoEjemplar):
    nombre = EN_TRANSITO
    descripcion = "Viajando entre sedes dentro de un remito"

    def recibir(self, ejemplar, sede, apartado: bool) -> None:
        ejemplar.ubicacion_actual = sede
        if apartado:
            ejemplar.cambiar_estado(RESERVADO)
        else:
            ejemplar.quedar_libre()

    def sacar_de_servicio(self, ejemplar) -> None:
        self._sacar(ejemplar)
