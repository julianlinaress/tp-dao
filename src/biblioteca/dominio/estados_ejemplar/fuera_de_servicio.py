from biblioteca.dominio.enums import EstadoFisico
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.estados_ejemplar.base import FUERA_DE_SERVICIO, EstadoEjemplar


class FueraDeServicio(EstadoEjemplar):
    nombre = FUERA_DE_SERVICIO
    descripcion = "Dañado, destruido o extraviado"

    def reparar(self, ejemplar) -> None:
        if ejemplar.estado_fisico is EstadoFisico.DESTRUIDO:
            raise ReglaIncumplida("Un ejemplar destruido no se puede reparar")
        ejemplar.estado_fisico = EstadoFisico.BUENO
        if ejemplar.ubicacion_actual is None:
            ejemplar.ubicacion_actual = ejemplar.sede
        ejemplar.quedar_libre()
