from biblioteca.dominio.estados_ejemplar.base import PENDIENTE_RETORNO, EstadoEjemplar


class PendienteRetorno(EstadoEjemplar):
    nombre = PENDIENTE_RETORNO
    descripcion = "Libre en una sede ajena, a la espera del remito de retorno"

    def enviar(self, ejemplar) -> None:
        self._enviar(ejemplar)

    def sacar_de_servicio(self, ejemplar) -> None:
        self._sacar(ejemplar)
