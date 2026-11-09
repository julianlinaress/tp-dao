"""Composición de la aplicación."""

from pathlib import Path

from biblioteca.config import MONTO_MULTA_POR_DIA, RUTA_BASE_DATOS, TOPE_MULTA
from biblioteca.dominio.estrategias_multa import MultaPorDiaConTope
from biblioteca.persistencia.base_datos import BaseDatos
from biblioteca.persistencia.repositorios import Repositorios
from biblioteca.servicios.administracion import SedeServicio, SocioServicio
from biblioteca.servicios.catalogo import CatalogoServicio
from biblioteca.servicios.logistica import LogisticaServicio
from biblioteca.servicios.prestamos import PrestamoServicio
from biblioteca.servicios.reloj import Reloj
from biblioteca.servicios.reportes import ReporteServicio
from biblioteca.servicios.reservas import ReservaServicio


class Servicios:
    def __init__(self, ruta: Path = RUTA_BASE_DATOS, reloj: Reloj | None = None) -> None:
        self.reloj = reloj or Reloj()
        self.repositorios = Repositorios(BaseDatos(ruta))
        r = self.repositorios
        self.sedes = SedeServicio(r)
        self.socios = SocioServicio(r, self.reloj)
        self.reservas = ReservaServicio(r, self.reloj)
        self.catalogo = CatalogoServicio(r, self.reservas)
        self.prestamos = PrestamoServicio(
            r, self.reloj, self.reservas, MultaPorDiaConTope(MONTO_MULTA_POR_DIA, TOPE_MULTA)
        )
        self.logistica = LogisticaServicio(r, self.reloj, self.reservas)
        self.reportes = ReporteServicio(r.base_datos, self.reloj)
