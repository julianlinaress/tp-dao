"""Parámetros de negocio definidos en el modelo de dominio."""

from pathlib import Path

DIAS_PRESTAMO_LOCAL = 14
DIAS_PRESTAMO_INTERBIBLIOTECARIO = 21
DIAS_RETIRO_RESERVA = 3
MAX_PRESTAMOS_ACTIVOS = 3

MONTO_MULTA_POR_DIA = 500.0
TOPE_MULTA = 15000.0

RUTA_BASE_DATOS = Path("biblioteca.db")
DIRECTORIO_SALIDAS = Path("salidas")
