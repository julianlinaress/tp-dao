from biblioteca.dominio.sede import Sede
from biblioteca.persistencia.dao import DAO

DUPLICADO = "Ya existe una sede con ese código"


class SedeDAO(DAO[Sede]):
    tabla = "sedes"
    nombre = "sede"
    orden = "nombre"

    def _desde_fila(self, fila) -> Sede:
        return Sede(
            id=fila["id"], codigo=fila["codigo"], nombre=fila["nombre"],
            direccion=fila["direccion"], telefono=fila["telefono"], email=fila["email"],
            horarios=fila["horarios"], es_activa=bool(fila["es_activa"]),
        )

    def crear(self, sede: Sede) -> Sede:
        sede.id = self._ejecutar(
            """INSERT INTO sedes (codigo, nombre, direccion, telefono, email, horarios, es_activa)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sede.codigo, sede.nombre, sede.direccion, sede.telefono, sede.email,
             sede.horarios, sede.es_activa),
            DUPLICADO,
        )
        return sede

    def actualizar(self, sede: Sede) -> None:
        self._ejecutar(
            """UPDATE sedes SET codigo = ?, nombre = ?, direccion = ?, telefono = ?,
               email = ?, horarios = ?, es_activa = ? WHERE id = ?""",
            (sede.codigo, sede.nombre, sede.direccion, sede.telefono, sede.email,
             sede.horarios, sede.es_activa, sede.id),
            DUPLICADO,
        )

    def listar_activas(self) -> list[Sede]:
        return self._mapear("SELECT * FROM sedes WHERE es_activa = 1 ORDER BY nombre")

    def operaciones_en_curso(self, sede_id: int) -> dict[str, int]:
        """Cuenta lo que todavía involucra a la sede e impediría darla de baja."""
        fila = self._uno(
            """SELECT
                 (SELECT COUNT(*) FROM prestamos
                   WHERE estado IN ('Solicitado', 'Activo')
                     AND ?1 IN (sede_origen_id, sede_destino_id)) AS prestamos,
                 (SELECT COUNT(*) FROM remitos
                   WHERE estado IN ('Generado', 'Empaquetado', 'EnTransito')
                     AND ?1 IN (sede_origen_id, sede_destino_id)) AS remitos,
                 (SELECT COUNT(*) FROM reservas
                   WHERE estado IN ('Pendiente', 'Activa') AND sede_id = ?1) AS reservas,
                 (SELECT COUNT(*) FROM ejemplares
                   WHERE (sede_id = ?1 AND estado_circulacion IN ('EnTransito', 'PendienteRetorno'))
                      OR (ubicacion_sede_id = ?1 AND sede_id <> ?1)) AS ejemplares""",
            (sede_id,),
        )
        return dict(fila)
