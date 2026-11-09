"""Validaciones comunes de datos de entrada y reglas de sede y socio."""

import re

from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.sede import Sede
from biblioteca.dominio.socio import Socio


def limpiar_textos(**campos: str) -> dict[str, str]:
    limpios = {nombre: (valor or "").strip() for nombre, valor in campos.items()}
    for nombre, valor in limpios.items():
        if not valor:
            raise ReglaIncumplida(f"El campo {nombre} es obligatorio")
    return limpios


def validar_email(email: str) -> None:
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ReglaIncumplida("El email no es válido")


def validar_dni(dni: str) -> None:
    if not re.fullmatch(r"\d{7,8}", dni):
        raise ReglaIncumplida("El DNI debe tener 7 u 8 dígitos")


def normalizar_isbn(isbn: str) -> str:
    normalizado = re.sub(r"[\s-]", "", isbn).upper()
    if not re.fullmatch(r"\d{13}|\d{9}[\dX]", normalizado):
        raise ReglaIncumplida("El ISBN debe tener 10 o 13 caracteres válidos")
    return normalizado


def exigir_sede_activa(sede: Sede) -> None:
    if not sede.esta_activa():
        raise ReglaIncumplida(f"La sede {sede.nombre} está dada de baja")


def exigir_socio_habilitado(socio: Socio) -> None:
    if not socio.es_habilitado:
        raise ReglaIncumplida(f"El socio {socio} está inhabilitado")
