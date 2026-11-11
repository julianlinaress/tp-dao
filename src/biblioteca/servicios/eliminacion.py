"""Reglas comunes para eliminar registros sin historial."""

from biblioteca.dominio.errores import ReglaIncumplida


def exigir_sin_referencias(
    que: str, referencias: dict[str, int], sugerencia: str = ""
) -> None:
    detalle = [f"{cantidad} {clave}" for clave, cantidad in referencias.items() if cantidad]
    if detalle:
        mensaje = f"No se puede eliminar {que}: tiene " + ", ".join(detalle) + " asociado(s)."
        raise ReglaIncumplida(f"{mensaje} {sugerencia}".strip())
