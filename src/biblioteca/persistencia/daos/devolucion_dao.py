from biblioteca.dominio.devolucion import Devolucion
from biblioteca.dominio.enums import EstadoFisico
from biblioteca.persistencia.dao import DAO, a_fecha, a_texto


class DevolucionDAO(DAO[Devolucion]):
    tabla = "devoluciones"
    nombre = "devolución"

    def __init__(self, base_datos, sedes) -> None:
        super().__init__(base_datos)
        self._sedes = sedes

    def _desde_fila(self, fila) -> Devolucion:
        return Devolucion(
            id=fila["id"], fecha=a_fecha(fila["fecha"]),
            estado_fisico=EstadoFisico(fila["estado_fisico"]),
            sede=self._sedes.requerir(fila["sede_id"]),
            observaciones=fila["observaciones"],
        )

    def crear(self, prestamo_id: int, devolucion: Devolucion) -> None:
        devolucion.id = self._ejecutar(
            """INSERT INTO devoluciones (prestamo_id, sede_id, fecha, estado_fisico, observaciones)
               VALUES (?, ?, ?, ?, ?)""",
            (prestamo_id, devolucion.sede.id, a_texto(devolucion.fecha),
             devolucion.estado_fisico.value, devolucion.observaciones),
            "El préstamo ya tiene una devolución registrada",
        )

    def obtener_por_prestamo(self, prestamo_id: int) -> Devolucion | None:
        resultado = self._mapear(
            "SELECT * FROM devoluciones WHERE prestamo_id = ?", (prestamo_id,)
        )
        return resultado[0] if resultado else None
