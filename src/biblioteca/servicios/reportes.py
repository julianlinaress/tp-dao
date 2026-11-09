"""Catálogo de reportes disponibles."""

from biblioteca.persistencia.daos.reportes_dao import ReportesDAO
from biblioteca.reportes.definiciones.catalogo import DisponibilidadPorSede
from biblioteca.reportes.definiciones.logistica import MovimientoEntreSedes, TasaDeEnvios
from biblioteca.reportes.definiciones.prestamos import (
    LibrosMasSolicitados,
    PrestamosActivosYEnTransito,
    VencidosYMultas,
)
from biblioteca.reportes.modelo import Reporte

TIPOS_DE_REPORTE = (
    PrestamosActivosYEnTransito,
    VencidosYMultas,
    LibrosMasSolicitados,
    DisponibilidadPorSede,
    TasaDeEnvios,
    MovimientoEntreSedes,
)


class ReporteServicio:
    def __init__(self, base_datos, reloj) -> None:
        dao = ReportesDAO(base_datos)
        self._reportes = [tipo(dao, reloj) for tipo in TIPOS_DE_REPORTE]

    def listar(self) -> list[Reporte]:
        return self._reportes
