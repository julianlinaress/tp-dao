"""Administración de sedes y socios."""

from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.sede import Sede
from biblioteca.dominio.socio import Socio
from biblioteca.servicios.eliminacion import exigir_sin_referencias
from biblioteca.servicios.validaciones import limpiar_textos, validar_dni, validar_email

DESCRIPCION_PENDIENTES = {
    "prestamos": "préstamo(s) sin cerrar",
    "remitos": "remito(s) activo(s)",
    "reservas": "reserva(s) vigente(s)",
    "ejemplares": "ejemplar(es) fuera de su sede",
}


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
        with self._r.transaccion():
            sede = self._r.sedes.requerir(sede_id)
            pendientes = self._r.sedes.operaciones_en_curso(sede_id)
            detalle = [
                f"{cantidad} {DESCRIPCION_PENDIENTES[clave]}"
                for clave, cantidad in pendientes.items()
                if cantidad
            ]
            if detalle:
                raise ReglaIncumplida(
                    f"No se puede dar de baja {sede.nombre}: tiene " + ", ".join(detalle)
                )
            sede.dar_baja()
            self._r.sedes.actualizar(sede)

    def reactivar(self, sede_id: int) -> None:
        sede = self._r.sedes.requerir(sede_id)
        sede.reactivar()
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

    def eliminar(self, socio_id: int) -> None:
        with self._r.transaccion():
            socio = self._r.socios.requerir(socio_id)
            exigir_sin_referencias(
                f"al socio {socio}", self._r.socios.referencias(socio_id),
                "Inhabilítelo para conservar su historial.",
            )
            self._r.socios.eliminar(socio_id)

    def listar(self, texto: str = "") -> list[Socio]:
        return self._r.socios.buscar(texto.strip()) if texto.strip() else self._r.socios.listar()
