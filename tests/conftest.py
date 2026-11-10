from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest

from biblioteca.contenedor import Servicios
from biblioteca.servicios.reloj import Reloj


class RelojFijo(Reloj):
    def __init__(self) -> None:
        self.momento = datetime(2026, 6, 1, 10, 0)

    def ahora(self) -> datetime:
        return self.momento

    def avanzar(self, **delta) -> None:
        self.momento += timedelta(**delta)


@dataclass
class Escenario:
    s: Servicios
    reloj: RelojFijo
    cba: object
    ros: object
    socio: object
    libro: object
    ejemplar: object

    def otro_socio(self, dni="30000002"):
        return self.s.socios.crear(dni=dni, nombre="Luis", apellido="Sosa", email="l@b.co")

    def otro_libro(self, isbn="9789500000002", sede=None, codigo="B-1"):
        libro = self.s.catalogo.crear_libro(
            isbn=isbn, titulo=f"Libro {isbn}", autor="Autor", edicion="1", genero="Ensayo", editorial="Ed"
        )
        ejemplar = self.s.catalogo.crear_ejemplar(libro.id, (sede or self.cba).id, codigo)
        return libro, ejemplar

    def forzar_baja(self, sede):
        """Deja la sede inactiva sin pasar por las reglas del servicio de sedes."""
        sede.dar_baja()
        self.s.repositorios.sedes.actualizar(sede)

    def estado_ejemplar(self, ejemplar=None):
        item = self.s.repositorios.ejemplares.requerir((ejemplar or self.ejemplar).id)
        return item.estado_circulacion.nombre


def crear_sede(s, codigo):
    return s.sedes.crear(
        codigo=codigo, nombre=f"Sede {codigo}", direccion="Calle 1", telefono="0351",
        email="s@b.co", horarios="8 a 18",
    )


@pytest.fixture
def esc(tmp_path) -> Escenario:
    reloj = RelojFijo()
    s = Servicios(tmp_path / "t.db", reloj)
    cba, ros = crear_sede(s, "CBA"), crear_sede(s, "ROS")
    socio = s.socios.crear(dni="30000001", nombre="Ana", apellido="Paz", email="a@b.co")
    libro = s.catalogo.crear_libro(
        isbn="978-950-00-0000-1", titulo="Rayuela", autor="Cortázar", edicion="1",
        genero="Novela", editorial="Sudamericana",
    )
    ejemplar = s.catalogo.crear_ejemplar(libro.id, cba.id, "a-1")
    return Escenario(s, reloj, cba, ros, socio, libro, ejemplar)
