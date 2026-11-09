"""Administración de sedes y socios."""

from biblioteca.dominio.sede import Sede
from biblioteca.dominio.socio import Socio
from biblioteca.servicios.validaciones import limpiar_textos, validar_dni, validar_email


class SedeServicio:
    def __init__(self, repositorios) -> None:
        self._r = repositorios

    @staticmethod
    def _validar(**datos: str) -> dict[str, str]:
        limpios = limpiar_textos(**datos)
        validar_email(limpios["email"])
        limpios["codigo"] = limpios["codigo"].upper()
        return limpios

    def crear(self, **datos: str) -> Sede:
        return self._r.sedes.crear(Sede(**self._validar(**datos)))

    def actualizar(self, sede_id: int, **datos: str) -> Sede:
        sede = self._r.sedes.requerir(sede_id)
        for campo, valor in self._validar(**datos).items():
            setattr(sede, campo, valor)
        self._r.sedes.actualizar(sede)
        return sede

    def dar_baja(self, sede_id: int) -> None:
        sede = self._r.sedes.requerir(sede_id)
        sede.dar_baja()
        self._r.sedes.actualizar(sede)

    def listar(self) -> list[Sede]:
        return self._r.sedes.listar()

    def listar_activas(self) -> list[Sede]:
        return self._r.sedes.listar_activas()


class SocioServicio:
    def __init__(self, repositorios, reloj) -> None:
        self._r = repositorios
        self._reloj = reloj

    @staticmethod
    def _validar(**datos: str) -> dict[str, str]:
        limpios = limpiar_textos(**datos)
        validar_dni(limpios["dni"])
        validar_email(limpios["email"])
        return limpios

    def crear(self, **datos: str) -> Socio:
        socio = Socio(fecha_alta=self._reloj.hoy(), **self._validar(**datos))
        return self._r.socios.crear(socio)

    def actualizar(self, socio_id: int, **datos: str) -> Socio:
        socio = self._r.socios.requerir(socio_id)
        for campo, valor in self._validar(**datos).items():
            setattr(socio, campo, valor)
        self._r.socios.actualizar(socio)
        return socio

    def cambiar_habilitacion(self, socio_id: int, habilitado: bool) -> None:
        socio = self._r.socios.requerir(socio_id)
        socio.habilitar() if habilitado else socio.deshabilitar()
        self._r.socios.actualizar(socio)

    def listar(self, texto: str = "") -> list[Socio]:
        return self._r.socios.buscar(texto.strip()) if texto.strip() else self._r.socios.listar()
