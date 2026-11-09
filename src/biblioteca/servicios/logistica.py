"""Generación de remitos y seguimiento de los envíos entre sedes."""

from biblioteca.dominio.detalle_remito import DetalleRemito
from biblioteca.dominio.enums import EstadoRecepcion, TipoRemito
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.prestamo import SolicitudPrestamo
from biblioteca.dominio.remito import Remito
from biblioteca.servicios.validaciones import exigir_sede_activa


class LogisticaServicio:
    def __init__(self, repositorios, reloj, reservas) -> None:
        self._r = repositorios
        self._reloj = reloj
        self._reservas = reservas

    def pendientes(self, tipo: TipoRemito) -> list[SolicitudPrestamo]:
        if tipo is TipoRemito.IDA:
            return self._r.prestamos.pendientes_de_ida()
        return self._r.prestamos.pendientes_de_retorno()

    def generar_remito(
        self, tipo: TipoRemito, prestamo_ids: list[int], observaciones: str = ""
    ) -> Remito:
        if not prestamo_ids:
            raise ReglaIncumplida("Un remito necesita al menos un préstamo")
        with self._r.transaccion():
            habilitados = {p.id: p for p in self.pendientes(tipo)}
            faltantes = [i for i in prestamo_ids if i not in habilitados]
            if faltantes:
                raise ReglaIncumplida(f"Préstamos que no admiten este remito: {faltantes}")
            prestamos = [habilitados[i] for i in prestamo_ids]

            origen, destino = self._ruta(tipo, prestamos[0])
            if any(self._ruta(tipo, p) != (origen, destino) for p in prestamos):
                raise ReglaIncumplida("Todos los préstamos deben compartir origen y destino")
            exigir_sede_activa(origen)
            exigir_sede_activa(destino)

            remito = Remito(
                tipo=tipo, fecha_emision=self._reloj.ahora(), sede_origen=origen,
                sede_destino=destino, observaciones=observaciones.strip(),
                detalles=[DetalleRemito(ejemplar=p.ejemplar, prestamo=p) for p in prestamos],
            )
            return self._r.remitos.crear(remito)

    @staticmethod
    def _ruta(tipo, prestamo):
        if tipo is TipoRemito.IDA:
            return prestamo.sede_origen, prestamo.sede_destino
        return prestamo.sede_destino, prestamo.sede_origen

    def empaquetar(self, remito_id: int) -> None:
        with self._r.transaccion():
            remito = self._r.remitos.requerir(remito_id)
            remito.empaquetar(self._reloj.ahora())
            self._r.remitos.actualizar(remito)

    def despachar(self, remito_id: int) -> None:
        with self._r.transaccion():
            remito = self._r.remitos.requerir(remito_id)
            exigir_sede_activa(remito.sede_origen)
            exigir_sede_activa(remito.sede_destino)
            remito.despachar(self._reloj.ahora())
            self._r.remitos.actualizar(remito)
            for detalle in remito.detalles:
                self._r.ejemplares.actualizar(detalle.ejemplar)

    def cancelar(self, remito_id: int) -> None:
        with self._r.transaccion():
            remito = self._r.remitos.requerir(remito_id)
            remito.cancelar(self._reloj.ahora())
            self._r.remitos.actualizar(remito)

    def recibir(self, remito_id: int, recepciones: dict | None = None) -> Remito:
        with self._r.transaccion():
            remito = self._r.remitos.requerir(remito_id)
            remito.recibir(recepciones or {}, self._reloj.ahora())
            self._r.remitos.actualizar(remito)
            for detalle in remito.detalles:
                self._r.ejemplares.actualizar(detalle.ejemplar)
                if remito.es_ida() and detalle.estado_recepcion is not EstadoRecepcion.OK:
                    detalle.prestamo.anular_por_incidencia()
                    self._r.prestamos.actualizar(detalle.prestamo)
                self._reservas.atender_liberado(detalle.ejemplar)
            return remito

    def listar(self) -> list[Remito]:
        return self._r.remitos.listar()

    def obtener(self, remito_id: int) -> Remito:
        return self._r.remitos.requerir(remito_id)
