"""Acceso a la base de datos SQLite."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from biblioteca.config import RUTA_BASE_DATOS


class BaseDatos:
    def __init__(self, ruta: Path = RUTA_BASE_DATOS) -> None:
        self._ruta = ruta
        self._conexion: sqlite3.Connection | None = None

    @contextmanager
    def transaccion(self) -> Iterator[sqlite3.Connection]:
        """Abre una transacción; las llamadas anidadas se suman a la actual."""
        if self._conexion is not None:
            yield self._conexion
            return

        self._conexion = self._abrir()
        try:
            with self._conexion:
                yield self._conexion
        finally:
            self._conexion.close()
            self._conexion = None

    def _abrir(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self._ruta)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion
