"""Clase base de los DAOs."""

from biblioteca.persistencia.base_datos import BaseDatos


class DAO:
    def __init__(self, base_datos: BaseDatos) -> None:
        self._base_datos = base_datos
