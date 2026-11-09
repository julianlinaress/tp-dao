"""Definición de las tablas."""

from biblioteca.persistencia.base_datos import BaseDatos

ESQUEMA = """
CREATE TABLE IF NOT EXISTS sedes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    direccion TEXT NOT NULL,
    telefono TEXT NOT NULL,
    email TEXT NOT NULL,
    horarios TEXT NOT NULL,
    es_activa INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS socios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dni TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT NOT NULL,
    fecha_alta TEXT NOT NULL,
    es_habilitado INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS libros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    autor TEXT NOT NULL,
    edicion TEXT NOT NULL,
    genero TEXT NOT NULL,
    editorial TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ejemplares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_inventario TEXT NOT NULL UNIQUE,
    libro_id INTEGER NOT NULL REFERENCES libros(id),
    sede_id INTEGER NOT NULL REFERENCES sedes(id),
    ubicacion_sede_id INTEGER REFERENCES sedes(id),
    estado_circulacion TEXT NOT NULL,
    estado_fisico TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prestamos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    socio_id INTEGER NOT NULL REFERENCES socios(id),
    ejemplar_id INTEGER NOT NULL REFERENCES ejemplares(id),
    sede_origen_id INTEGER NOT NULL REFERENCES sedes(id),
    sede_destino_id INTEGER NOT NULL REFERENCES sedes(id),
    tipo TEXT NOT NULL,
    fecha_solicitud TEXT NOT NULL,
    fecha_retiro TEXT,
    fecha_vencimiento TEXT,
    estado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS devoluciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prestamo_id INTEGER NOT NULL UNIQUE REFERENCES prestamos(id),
    sede_id INTEGER NOT NULL REFERENCES sedes(id),
    fecha TEXT NOT NULL,
    estado_fisico TEXT NOT NULL,
    observaciones TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS multas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prestamo_id INTEGER NOT NULL UNIQUE REFERENCES prestamos(id),
    dias_atraso INTEGER NOT NULL CHECK (dias_atraso > 0),
    monto REAL NOT NULL,
    es_pagada INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    socio_id INTEGER NOT NULL REFERENCES socios(id),
    libro_id INTEGER NOT NULL REFERENCES libros(id),
    sede_id INTEGER NOT NULL REFERENCES sedes(id),
    ejemplar_id INTEGER REFERENCES ejemplares(id),
    fecha TEXT NOT NULL,
    fecha_vencimiento TEXT,
    estado TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS reserva_vigente_unica
    ON reservas(socio_id, libro_id, sede_id)
    WHERE estado IN ('Pendiente', 'Activa');
CREATE TABLE IF NOT EXISTS remitos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    fecha_emision TEXT NOT NULL,
    observaciones TEXT NOT NULL DEFAULT '',
    estado TEXT NOT NULL,
    sede_origen_id INTEGER NOT NULL REFERENCES sedes(id),
    sede_destino_id INTEGER NOT NULL REFERENCES sedes(id)
);
CREATE TABLE IF NOT EXISTS detalles_remito (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remito_id INTEGER NOT NULL REFERENCES remitos(id),
    prestamo_id INTEGER NOT NULL REFERENCES prestamos(id),
    ejemplar_id INTEGER NOT NULL REFERENCES ejemplares(id),
    estado_recepcion TEXT,
    observaciones TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS cambios_estado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remito_id INTEGER NOT NULL REFERENCES remitos(id),
    estado_anterior TEXT NOT NULL,
    estado_nuevo TEXT NOT NULL,
    fecha_hora_inicio TEXT NOT NULL,
    fecha_hora_fin TEXT NOT NULL
);
"""


def crear_tablas(base_datos: BaseDatos) -> None:
    with base_datos.transaccion() as conexion:
        conexion.executescript(ESQUEMA)
