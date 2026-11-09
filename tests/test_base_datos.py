import sqlite3

import pytest

from biblioteca.persistencia.base_datos import BaseDatos


@pytest.fixture
def base_datos(tmp_path):
    bd = BaseDatos(tmp_path / "test.db")
    with bd.transaccion() as cx:
        cx.execute("CREATE TABLE sedes (id INTEGER PRIMARY KEY, codigo TEXT UNIQUE)")
        cx.execute("CREATE TABLE ejemplares (sede_id INTEGER NOT NULL REFERENCES sedes(id))")
    return bd


def contar_sedes(bd):
    with bd.transaccion() as cx:
        return cx.execute("SELECT COUNT(*) AS total FROM sedes").fetchone()["total"]


def test_confirma_al_terminar(base_datos):
    with base_datos.transaccion() as cx:
        cx.execute("INSERT INTO sedes (codigo) VALUES (?)", ("CBA",))
    assert contar_sedes(base_datos) == 1


def test_error_en_transaccion_anidada_revierte_todo(base_datos):
    with pytest.raises(ValueError):
        with base_datos.transaccion() as externa:
            externa.execute("INSERT INTO sedes (codigo) VALUES (?)", ("CBA",))
            with base_datos.transaccion() as interna:
                assert interna is externa
                raise ValueError
    assert contar_sedes(base_datos) == 0


def test_claves_foraneas_activas(base_datos):
    with pytest.raises(sqlite3.IntegrityError):
        with base_datos.transaccion() as cx:
            cx.execute("INSERT INTO ejemplares (sede_id) VALUES (?)", (999,))


def test_cierra_la_conexion(base_datos):
    with base_datos.transaccion() as cx:
        pass
    with pytest.raises(sqlite3.ProgrammingError):
        cx.execute("SELECT 1")
