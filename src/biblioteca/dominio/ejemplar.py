from dataclasses import dataclass, field

from biblioteca.dominio.entidad import Entidad
from biblioteca.dominio.enums import EstadoFisico
from biblioteca.dominio.estados_ejemplar import (
    DISPONIBLE,
    PENDIENTE_RETORNO,
    Disponible,
    EstadoEjemplar,
)
from biblioteca.dominio.libro import Libro
from biblioteca.dominio.sede import Sede


@dataclass(kw_only=True, eq=False)
class Ejemplar(Entidad):
    codigo_inventario: str
    libro: Libro
    sede: Sede
    ubicacion_actual: Sede | None
    estado_circulacion: EstadoEjemplar = field(default_factory=Disponible)
    estado_fisico: EstadoFisico = EstadoFisico.BUENO

    def cambiar_estado(self, nombre: str) -> None:
        self.estado_circulacion = EstadoEjemplar.desde_nombre(nombre)

    def quedar_libre(self) -> None:
        en_su_sede = self.ubicacion_actual == self.sede
        self.cambiar_estado(DISPONIBLE if en_su_sede else PENDIENTE_RETORNO)

    def esta_disponible(self) -> bool:
        return self.estado_circulacion.nombre == DISPONIBLE

    def puede_entregarse(self) -> bool:
        return self.esta_disponible() and not self.estado_fisico.requiere_reparacion

    def prestar(self) -> None:
        self.estado_circulacion.prestar(self)

    def devolver(self, estado_fisico: EstadoFisico) -> None:
        self.estado_circulacion.devolver(self, estado_fisico)

    def reservar(self) -> None:
        self.estado_circulacion.reservar(self)

    def liberar(self) -> None:
        self.estado_circulacion.liberar(self)

    def enviar(self) -> None:
        self.estado_circulacion.enviar(self)

    def recibir(self, sede: Sede, apartado: bool = False) -> None:
        self.estado_circulacion.recibir(self, sede, apartado)

    def sacar_de_servicio(self, estado_fisico: EstadoFisico | None = None) -> None:
        self.estado_circulacion.sacar_de_servicio(self)
        if estado_fisico is not None:
            self.estado_fisico = estado_fisico

    def reparar(self) -> None:
        self.estado_circulacion.reparar(self)
