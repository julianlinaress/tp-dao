from biblioteca.dominio.ejemplar import Ejemplar
from biblioteca.dominio.enums import EstadoFisico
from biblioteca.dominio.estados_ejemplar import EstadoEjemplar
from biblioteca.persistencia.dao import DAO

DUPLICADO = "Ya existe un ejemplar con ese código de inventario"


class EjemplarDAO(DAO[Ejemplar]):
    tabla = "ejemplares"
    nombre = "ejemplar"
    orden = "codigo_inventario"

    def __init__(self, base_datos, sedes, libros) -> None:
        super().__init__(base_datos)
        self._sedes = sedes
        self._libros = libros

    def _desde_fila(self, fila) -> Ejemplar:
        ubicacion = fila["ubicacion_sede_id"]
        return Ejemplar(
            id=fila["id"],
            codigo_inventario=fila["codigo_inventario"],
            libro=self._libros.requerir(fila["libro_id"]),
            sede=self._sedes.requerir(fila["sede_id"]),
            ubicacion_actual=self._sedes.requerir(ubicacion) if ubicacion else None,
            estado_circulacion=EstadoEjemplar.desde_nombre(fila["estado_circulacion"]),
            estado_fisico=EstadoFisico(fila["estado_fisico"]),
        )

    def crear(self, ejemplar: Ejemplar) -> Ejemplar:
        ejemplar.id = self._ejecutar(
            """INSERT INTO ejemplares (codigo_inventario, libro_id, sede_id, ubicacion_sede_id,
               estado_circulacion, estado_fisico) VALUES (?, ?, ?, ?, ?, ?)""",
            (ejemplar.codigo_inventario, ejemplar.libro.id, ejemplar.sede.id,
             ejemplar.ubicacion_actual.id, ejemplar.estado_circulacion.nombre,
             ejemplar.estado_fisico.value),
            DUPLICADO,
        )
        return ejemplar

    def actualizar(self, ejemplar: Ejemplar) -> None:
        ubicacion = ejemplar.ubicacion_actual
        self._ejecutar(
            """UPDATE ejemplares SET codigo_inventario = ?, ubicacion_sede_id = ?,
               estado_circulacion = ?, estado_fisico = ? WHERE id = ?""",
            (ejemplar.codigo_inventario, ubicacion.id if ubicacion else None,
             ejemplar.estado_circulacion.nombre, ejemplar.estado_fisico.value, ejemplar.id),
            DUPLICADO,
        )

    def listar_por_libro_y_sede(self, libro_id: int, sede_id: int) -> list[Ejemplar]:
        return self._mapear(
            "SELECT * FROM ejemplares WHERE libro_id = ? AND sede_id = ? ORDER BY id",
            (libro_id, sede_id),
        )

    def disponibilidad(self, libro_id: int | None, sede_id: int | None) -> list[dict]:
        filas = self._todos(
            """SELECT l.titulo, s.nombre AS sede, COUNT(*) AS total,
                      SUM(e.estado_circulacion = 'Disponible') AS disponibles
               FROM ejemplares e
               JOIN libros l ON l.id = e.libro_id
               JOIN sedes s ON s.id = e.sede_id
               WHERE (?1 IS NULL OR e.libro_id = ?1) AND (?2 IS NULL OR e.sede_id = ?2)
               GROUP BY l.id, s.id ORDER BY l.titulo, s.nombre""",
            (libro_id, sede_id),
        )
        return [dict(fila) for fila in filas]
