from biblioteca.dominio.socio import Socio
from biblioteca.persistencia.dao import DAO, a_fecha, a_texto

DUPLICADO = "Ya existe un socio con ese DNI"


class SocioDAO(DAO[Socio]):
    tabla = "socios"
    nombre = "socio"
    orden = "apellido, nombre"

    def _desde_fila(self, fila) -> Socio:
        return Socio(
            id=fila["id"], dni=fila["dni"], nombre=fila["nombre"], apellido=fila["apellido"],
            email=fila["email"], fecha_alta=a_fecha(fila["fecha_alta"]),
            es_habilitado=bool(fila["es_habilitado"]),
        )

    def crear(self, socio: Socio) -> Socio:
        socio.id = self._ejecutar(
            """INSERT INTO socios (dni, nombre, apellido, email, fecha_alta, es_habilitado)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (socio.dni, socio.nombre, socio.apellido, socio.email,
             a_texto(socio.fecha_alta), socio.es_habilitado),
            DUPLICADO,
        )
        return socio

    def actualizar(self, socio: Socio) -> None:
        self._ejecutar(
            """UPDATE socios SET dni = ?, nombre = ?, apellido = ?, email = ?,
               es_habilitado = ? WHERE id = ?""",
            (socio.dni, socio.nombre, socio.apellido, socio.email,
             socio.es_habilitado, socio.id),
            DUPLICADO,
        )

    def referencias(self, socio_id: int) -> dict[str, int]:
        """Cuenta el historial que impide eliminar al socio."""
        fila = self._uno(
            """SELECT (SELECT COUNT(*) FROM prestamos WHERE socio_id = ?1) AS prestamos,
                      (SELECT COUNT(*) FROM reservas WHERE socio_id = ?1) AS reservas""",
            (socio_id,),
        )
        return dict(fila)

    def buscar(self, texto: str) -> list[Socio]:
        patron = f"%{texto}%"
        return self._mapear(
            """SELECT * FROM socios WHERE dni LIKE ? OR nombre LIKE ? OR apellido LIKE ?
               ORDER BY apellido, nombre""",
            (patron, patron, patron),
        )
