"""Armado de los DAOs y sus dependencias."""

from biblioteca.persistencia.base_datos import BaseDatos
from biblioteca.persistencia.daos.devolucion_dao import DevolucionDAO
from biblioteca.persistencia.daos.ejemplar_dao import EjemplarDAO
from biblioteca.persistencia.daos.libro_dao import LibroDAO
from biblioteca.persistencia.daos.multa_dao import MultaDAO
from biblioteca.persistencia.daos.prestamo_dao import PrestamoDAO
from biblioteca.persistencia.daos.remito_dao import (
    CambioEstadoDAO,
    DetalleRemitoDAO,
    RemitoDAO,
)
from biblioteca.persistencia.daos.reserva_dao import ReservaDAO
from biblioteca.persistencia.daos.sede_dao import SedeDAO
from biblioteca.persistencia.daos.socio_dao import SocioDAO
from biblioteca.persistencia.esquema import crear_tablas


class Repositorios:
    def __init__(self, base_datos: BaseDatos) -> None:
        crear_tablas(base_datos)
        self.base_datos = base_datos
        self.sedes = SedeDAO(base_datos)
        self.socios = SocioDAO(base_datos)
        self.libros = LibroDAO(base_datos)
        self.ejemplares = EjemplarDAO(base_datos, self.sedes, self.libros)
        self.devoluciones = DevolucionDAO(base_datos, self.sedes)
        self.multas = MultaDAO(base_datos)
        self.prestamos = PrestamoDAO(
            base_datos, self.socios, self.ejemplares, self.sedes, self.devoluciones, self.multas
        )
        self.reservas = ReservaDAO(
            base_datos, self.socios, self.libros, self.sedes, self.ejemplares
        )
        self.detalles = DetalleRemitoDAO(base_datos, self.prestamos)
        self.cambios = CambioEstadoDAO(base_datos)
        self.remitos = RemitoDAO(base_datos, self.sedes, self.detalles, self.cambios)

    def transaccion(self):
        return self.base_datos.transaccion()
