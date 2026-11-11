"""Clase base de los DAOs."""

import sqlite3
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import ClassVar

from biblioteca.dominio.errores import RegistroDuplicado, RegistroNoEncontrado
from biblioteca.persistencia.base_datos import BaseDatos


def a_fecha(valor: str | None) -> date | None:
    return date.fromisoformat(valor) if valor else None


def a_fecha_hora(valor: str) -> datetime:
    return datetime.fromisoformat(valor)


def a_texto(valor: date | datetime | None) -> str | None:
    return valor.isoformat() if valor else None


class Consultas:
    """Ejecución de SQL con parámetros, común a todos los DAOs."""

    def __init__(self, base_datos: BaseDatos) -> None:
        self._base_datos = base_datos

    def _uno(self, sql: str, parametros: tuple = ()) -> sqlite3.Row | None:
        with self._base_datos.transaccion() as conexion:
            return conexion.execute(sql, parametros).fetchone()

    def _todos(self, sql: str, parametros: tuple = ()) -> list[sqlite3.Row]:
        with self._base_datos.transaccion() as conexion:
            return conexion.execute(sql, parametros).fetchall()

    def _ejecutar(self, sql: str, parametros: tuple, duplicado: str = "") -> int:
        try:
            with self._base_datos.transaccion() as conexion:
                return conexion.execute(sql, parametros).lastrowid
        except sqlite3.IntegrityError as error:
            if duplicado and "UNIQUE" in str(error):
                raise RegistroDuplicado(duplicado) from error
            raise


class DAO[T](Consultas, ABC):
    tabla: ClassVar[str]
    nombre: ClassVar[str]
    orden: ClassVar[str] = "id"

    @abstractmethod
    def _desde_fila(self, fila: sqlite3.Row) -> T:
        pass

    def _mapear(self, sql: str, parametros: tuple = ()) -> list[T]:
        with self._base_datos.transaccion():
            return [self._desde_fila(fila) for fila in self._todos(sql, parametros)]

    def obtener_por_id(self, id_: int) -> T | None:
        with self._base_datos.transaccion():
            fila = self._uno(f"SELECT * FROM {self.tabla} WHERE id = ?", (id_,))
            return self._desde_fila(fila) if fila else None

    def requerir(self, id_: int) -> T:
        entidad = self.obtener_por_id(id_)
        if entidad is None:
            raise RegistroNoEncontrado(f"No existe {self.nombre} con id {id_}")
        return entidad

    def eliminar(self, id_: int) -> None:
        self._ejecutar(f"DELETE FROM {self.tabla} WHERE id = ?", (id_,))

    def listar(self) -> list[T]:
        return self._mapear(f"SELECT * FROM {self.tabla} ORDER BY {self.orden}")
