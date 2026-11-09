from datetime import date

from biblioteca.dominio.enums import EstadoPrestamo
from biblioteca.dominio.prestamo import SolicitudPrestamo
from biblioteca.dominio.tipo_prestamo import TIPOS_PRESTAMO
from biblioteca.persistencia.dao import DAO, a_fecha, a_texto

SIN_REMITO_ACTIVO = """NOT EXISTS (
    SELECT 1 FROM detalles_remito d JOIN remitos r ON r.id = d.remito_id
    WHERE d.ejemplar_id = p.ejemplar_id AND r.estado IN ('Generado', 'Empaquetado', 'EnTransito')
)"""


class PrestamoDAO(DAO[SolicitudPrestamo]):
    tabla = "prestamos"
    nombre = "préstamo"
    orden = "id DESC"

    def __init__(self, base_datos, socios, ejemplares, sedes, devoluciones, multas) -> None:
        super().__init__(base_datos)
        self._socios = socios
        self._ejemplares = ejemplares
        self._sedes = sedes
        self._devoluciones = devoluciones
        self._multas = multas

    def _desde_fila(self, fila) -> SolicitudPrestamo:
        return SolicitudPrestamo(
            id=fila["id"],
            socio=self._socios.requerir(fila["socio_id"]),
            ejemplar=self._ejemplares.requerir(fila["ejemplar_id"]),
            sede_origen=self._sedes.requerir(fila["sede_origen_id"]),
            sede_destino=self._sedes.requerir(fila["sede_destino_id"]),
            tipo=TIPOS_PRESTAMO[fila["tipo"]],
            fecha_solicitud=a_fecha(fila["fecha_solicitud"]),
            fecha_retiro=a_fecha(fila["fecha_retiro"]),
            fecha_vencimiento=a_fecha(fila["fecha_vencimiento"]),
            estado=EstadoPrestamo(fila["estado"]),
            devolucion=self._devoluciones.obtener_por_prestamo(fila["id"]),
            multa=self._multas.obtener_por_prestamo(fila["id"]),
        )

    def crear(self, prestamo: SolicitudPrestamo) -> SolicitudPrestamo:
        prestamo.id = self._ejecutar(
            """INSERT INTO prestamos (socio_id, ejemplar_id, sede_origen_id, sede_destino_id,
               tipo, fecha_solicitud, fecha_retiro, fecha_vencimiento, estado)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (prestamo.socio.id, prestamo.ejemplar.id, prestamo.sede_origen.id,
             prestamo.sede_destino.id, prestamo.tipo.nombre, a_texto(prestamo.fecha_solicitud),
             a_texto(prestamo.fecha_retiro), a_texto(prestamo.fecha_vencimiento),
             prestamo.estado.value),
        )
        return prestamo

    def actualizar(self, prestamo: SolicitudPrestamo) -> None:
        self._ejecutar(
            "UPDATE prestamos SET fecha_retiro = ?, fecha_vencimiento = ?, estado = ? WHERE id = ?",
            (a_texto(prestamo.fecha_retiro), a_texto(prestamo.fecha_vencimiento),
             prestamo.estado.value, prestamo.id),
        )
        if prestamo.devolucion and prestamo.devolucion.id is None:
            self._devoluciones.crear(prestamo.id, prestamo.devolucion)
        if prestamo.multa and prestamo.multa.id is None:
            self._multas.crear(prestamo.id, prestamo.multa)

    def contar_vigentes(self, socio_id: int) -> int:
        fila = self._uno(
            """SELECT COUNT(*) AS total FROM prestamos
               WHERE socio_id = ? AND estado IN ('Solicitado', 'Activo')""",
            (socio_id,),
        )
        return fila["total"]

    def tiene_vencidos(self, socio_id: int, hoy: date) -> bool:
        fila = self._uno(
            """SELECT 1 FROM prestamos WHERE socio_id = ? AND estado = 'Activo'
               AND fecha_vencimiento < ? LIMIT 1""",
            (socio_id, a_texto(hoy)),
        )
        return fila is not None

    def listar_por_estado(self, estado: EstadoPrestamo) -> list[SolicitudPrestamo]:
        return self._mapear(
            "SELECT * FROM prestamos WHERE estado = ? ORDER BY id DESC", (estado.value,)
        )

    def listar_con_multa(self) -> list[SolicitudPrestamo]:
        return self._mapear(
            """SELECT p.* FROM prestamos p JOIN multas m ON m.prestamo_id = p.id
               ORDER BY m.es_pagada, p.id DESC"""
        )

    def pendientes_de_ida(self) -> list[SolicitudPrestamo]:
        return self._mapear(
            f"""SELECT p.* FROM prestamos p JOIN ejemplares e ON e.id = p.ejemplar_id
                WHERE p.tipo = 'Interbibliotecario' AND p.estado = 'Solicitado'
                AND e.estado_circulacion = 'Reservado' AND e.ubicacion_sede_id = p.sede_origen_id
                AND {SIN_REMITO_ACTIVO} ORDER BY p.id"""
        )

    def pendientes_de_retorno(self) -> list[SolicitudPrestamo]:
        return self._mapear(
            f"""SELECT p.* FROM prestamos p JOIN ejemplares e ON e.id = p.ejemplar_id
                WHERE p.tipo = 'Interbibliotecario' AND e.estado_circulacion = 'PendienteRetorno'
                AND p.id = (SELECT MAX(id) FROM prestamos WHERE ejemplar_id = e.id)
                AND {SIN_REMITO_ACTIVO} ORDER BY p.id"""
        )
