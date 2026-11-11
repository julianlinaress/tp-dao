"""Catálogo de libros, ejemplares físicos y disponibilidad."""

from biblioteca.dominio.ejemplar import Ejemplar
from biblioteca.dominio.enums import EstadoFisico
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.libro import Libro
from biblioteca.servicios.eliminacion import exigir_sin_referencias
from biblioteca.servicios.validaciones import limpiar_textos, normalizar_isbn


class CatalogoServicio:
    def __init__(self, repositorios, reservas) -> None:
        self._r = repositorios
        self._reservas = reservas

    @staticmethod
    def _validar_libro(**datos: str) -> dict[str, str]:
        limpios = limpiar_textos(**datos)
        limpios["isbn"] = normalizar_isbn(limpios["isbn"])
        return limpios

    def crear_libro(self, **datos: str) -> Libro:
        return self._r.libros.crear(Libro(**self._validar_libro(**datos)))

    def actualizar_libro(self, libro_id: int, **datos: str) -> Libro:
        libro = self._r.libros.requerir(libro_id)
        for campo, valor in self._validar_libro(**datos).items():
            setattr(libro, campo, valor)
        self._r.libros.actualizar(libro)
        return libro

    def eliminar_libro(self, libro_id: int) -> None:
        with self._r.transaccion():
            libro = self._r.libros.requerir(libro_id)
            exigir_sin_referencias(
                f"el libro «{libro.titulo}»", self._r.libros.referencias(libro_id),
                "Elimine antes sus ejemplares.",
            )
            self._r.libros.eliminar(libro_id)

    def eliminar_ejemplar(self, ejemplar_id: int) -> None:
        with self._r.transaccion():
            ejemplar = self._r.ejemplares.requerir(ejemplar_id)
            exigir_sin_referencias(
                f"el ejemplar {ejemplar.codigo_inventario}",
                self._r.ejemplares.referencias(ejemplar_id),
            )
            self._r.ejemplares.eliminar(ejemplar_id)

    def listar_libros(self) -> list[Libro]:
        return self._r.libros.listar()

    def generos(self) -> list[str]:
        return self._r.libros.generos()

    def crear_ejemplar(
        self, libro_id: int, sede_id: int, codigo_inventario: str,
        estado_fisico: EstadoFisico = EstadoFisico.BUENO,
    ) -> Ejemplar:
        sede = self._r.sedes.requerir(sede_id)
        ejemplar = Ejemplar(
            codigo_inventario=limpiar_textos(codigo=codigo_inventario)["codigo"].upper(),
            libro=self._r.libros.requerir(libro_id),
            sede=sede,
            ubicacion_actual=sede,
        )
        if estado_fisico.requiere_reparacion:
            ejemplar.sacar_de_servicio(estado_fisico)
        else:
            ejemplar.estado_fisico = estado_fisico
        return self._r.ejemplares.crear(ejemplar)

    def listar_ejemplares(self) -> list[Ejemplar]:
        return self._r.ejemplares.listar()

    def sacar_de_servicio(self, ejemplar_id: int, estado_fisico: EstadoFisico) -> None:
        with self._r.transaccion():
            ejemplar = self._r.ejemplares.requerir(ejemplar_id)
            if not ejemplar.esta_disponible():
                raise ReglaIncumplida("Solo se sacan de servicio ejemplares disponibles")
            ejemplar.sacar_de_servicio(estado_fisico)
            self._r.ejemplares.actualizar(ejemplar)

    def reparar(self, ejemplar_id: int) -> None:
        with self._r.transaccion():
            ejemplar = self._r.ejemplares.requerir(ejemplar_id)
            ejemplar.reparar()
            self._r.ejemplares.actualizar(ejemplar)
            self._reservas.atender_liberado(ejemplar)

    def disponibilidad(self, libro_id: int | None = None, sede_id: int | None = None) -> list[dict]:
        return self._r.ejemplares.disponibilidad(libro_id, sede_id)
