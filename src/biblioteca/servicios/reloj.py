"""Fuente de fecha y hora, reemplazable en pruebas y datos de ejemplo."""

from datetime import date, datetime


class Reloj:
    def ahora(self) -> datetime:
        return datetime.now()

    def hoy(self) -> date:
        return self.ahora().date()
