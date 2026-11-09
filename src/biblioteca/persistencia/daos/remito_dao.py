from biblioteca.dominio.cambio_estado import CambioEstado
from biblioteca.dominio.detalle_remito import DetalleRemito
from biblioteca.dominio.enums import EstadoRecepcion, TipoRemito
from biblioteca.dominio.estados_remito import EstadoRemito
from biblioteca.dominio.remito import Remito
from biblioteca.persistencia.dao import DAO, Consultas, a_fecha_hora, a_texto


class DetalleRemitoDAO(DAO[DetalleRemito]):
    tabla = "detalles_remito"
    nombre = "detalle de remito"

    def __init__(self, base_datos, prestamos) -> None:
        super().__init__(base_datos)
        self._prestamos = prestamos

    def _desde_fila(self, fila) -> DetalleRemito:
        prestamo = self._prestamos.requerir(fila["prestamo_id"])
        recepcion = fila["estado_recepcion"]
        return DetalleRemito(
            id=fila["id"], ejemplar=prestamo.ejemplar, prestamo=prestamo,
            estado_recepcion=EstadoRecepcion(recepcion) if recepcion else None,
            observaciones=fila["observaciones"],
        )

    def crear(self, remito_id: int, detalle: DetalleRemito) -> None:
        detalle.id = self._ejecutar(
            "INSERT INTO detalles_remito (remito_id, prestamo_id, ejemplar_id) VALUES (?, ?, ?)",
            (remito_id, detalle.prestamo.id, detalle.ejemplar.id),
        )

    def actualizar(self, detalle: DetalleRemito) -> None:
        recepcion = detalle.estado_recepcion
        self._ejecutar(
            "UPDATE detalles_remito SET estado_recepcion = ?, observaciones = ? WHERE id = ?",
            (recepcion.value if recepcion else None, detalle.observaciones, detalle.id),
        )

    def obtener_por_remito(self, remito_id: int) -> list[DetalleRemito]:
        return self._mapear(
            "SELECT * FROM detalles_remito WHERE remito_id = ? ORDER BY id", (remito_id,)
        )

    def ejemplar_en_remito_activo(self, ejemplar_id: int) -> bool:
        fila = self._uno(
            """SELECT 1 FROM detalles_remito d JOIN remitos r ON r.id = d.remito_id
               WHERE d.ejemplar_id = ? AND r.estado IN ('Generado', 'Empaquetado', 'EnTransito')
               LIMIT 1""",
            (ejemplar_id,),
        )
        return fila is not None


class CambioEstadoDAO(Consultas):
    def crear(self, remito_id: int, cambio: CambioEstado) -> None:
        cambio.id = self._ejecutar(
            """INSERT INTO cambios_estado (remito_id, estado_anterior, estado_nuevo,
               fecha_hora_inicio, fecha_hora_fin) VALUES (?, ?, ?, ?, ?)""",
            (remito_id, cambio.estado_anterior, cambio.estado_nuevo,
             a_texto(cambio.fecha_hora_inicio), a_texto(cambio.fecha_hora_fin)),
        )

    def obtener_por_remito(self, remito_id: int) -> list[CambioEstado]:
        filas = self._todos(
            "SELECT * FROM cambios_estado WHERE remito_id = ? ORDER BY id", (remito_id,)
        )
        return [
            CambioEstado(
                id=fila["id"], estado_anterior=fila["estado_anterior"],
                estado_nuevo=fila["estado_nuevo"],
                fecha_hora_inicio=a_fecha_hora(fila["fecha_hora_inicio"]),
                fecha_hora_fin=a_fecha_hora(fila["fecha_hora_fin"]),
            )
            for fila in filas
        ]


class RemitoDAO(DAO[Remito]):
    tabla = "remitos"
    nombre = "remito"
    orden = "id DESC"

    def __init__(self, base_datos, sedes, detalles, cambios) -> None:
        super().__init__(base_datos)
        self._sedes = sedes
        self._detalles = detalles
        self._cambios = cambios

    def _desde_fila(self, fila) -> Remito:
        return Remito(
            id=fila["id"], tipo=TipoRemito(fila["tipo"]),
            fecha_emision=a_fecha_hora(fila["fecha_emision"]),
            observaciones=fila["observaciones"],
            estado=EstadoRemito.desde_nombre(fila["estado"]),
            sede_origen=self._sedes.requerir(fila["sede_origen_id"]),
            sede_destino=self._sedes.requerir(fila["sede_destino_id"]),
            detalles=self._detalles.obtener_por_remito(fila["id"]),
            cambios=self._cambios.obtener_por_remito(fila["id"]),
        )

    def crear(self, remito: Remito) -> Remito:
        with self._base_datos.transaccion():
            remito.id = self._ejecutar(
                """INSERT INTO remitos (tipo, fecha_emision, observaciones, estado,
                   sede_origen_id, sede_destino_id) VALUES (?, ?, ?, ?, ?, ?)""",
                (remito.tipo.value, a_texto(remito.fecha_emision), remito.observaciones,
                 remito.estado.nombre, remito.sede_origen.id, remito.sede_destino.id),
            )
            for detalle in remito.detalles:
                self._detalles.crear(remito.id, detalle)
        return remito

    def actualizar(self, remito: Remito) -> None:
        with self._base_datos.transaccion():
            self._ejecutar(
                "UPDATE remitos SET estado = ? WHERE id = ?", (remito.estado.nombre, remito.id)
            )
            for detalle in remito.detalles:
                self._detalles.actualizar(detalle)
            for cambio in remito.cambios:
                if cambio.id is None:
                    self._cambios.crear(remito.id, cambio)
