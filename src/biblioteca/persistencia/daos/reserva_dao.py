from biblioteca.dominio.enums import EstadoReserva
from biblioteca.dominio.reserva import Reserva
from biblioteca.persistencia.dao import DAO, a_fecha, a_texto


class ReservaDAO(DAO[Reserva]):
    tabla = "reservas"
    nombre = "reserva"
    orden = "id DESC"

    def __init__(self, base_datos, socios, libros, sedes, ejemplares) -> None:
        super().__init__(base_datos)
        self._socios = socios
        self._libros = libros
        self._sedes = sedes
        self._ejemplares = ejemplares

    def _desde_fila(self, fila) -> Reserva:
        ejemplar = fila["ejemplar_id"]
        return Reserva(
            id=fila["id"],
            socio=self._socios.requerir(fila["socio_id"]),
            libro=self._libros.requerir(fila["libro_id"]),
            sede=self._sedes.requerir(fila["sede_id"]),
            fecha=a_fecha(fila["fecha"]),
            fecha_vencimiento=a_fecha(fila["fecha_vencimiento"]),
            estado=EstadoReserva(fila["estado"]),
            ejemplar=self._ejemplares.requerir(ejemplar) if ejemplar else None,
        )

    def crear(self, reserva: Reserva) -> Reserva:
        reserva.id = self._ejecutar(
            """INSERT INTO reservas (socio_id, libro_id, sede_id, fecha, estado)
               VALUES (?, ?, ?, ?, ?)""",
            (reserva.socio.id, reserva.libro.id, reserva.sede.id, a_texto(reserva.fecha),
             reserva.estado.value),
            "El socio ya tiene una reserva vigente de ese libro en esa sede",
        )
        return reserva

    def actualizar(self, reserva: Reserva) -> None:
        ejemplar = reserva.ejemplar
        self._ejecutar(
            "UPDATE reservas SET ejemplar_id = ?, fecha_vencimiento = ?, estado = ? WHERE id = ?",
            (ejemplar.id if ejemplar else None, a_texto(reserva.fecha_vencimiento),
             reserva.estado.value, reserva.id),
        )

    def siguiente_pendiente(self, libro_id: int, sede_id: int) -> Reserva | None:
        resultado = self._mapear(
            """SELECT * FROM reservas WHERE libro_id = ? AND sede_id = ? AND estado = 'Pendiente'
               ORDER BY fecha, id LIMIT 1""",
            (libro_id, sede_id),
        )
        return resultado[0] if resultado else None

    def listar_activas(self) -> list[Reserva]:
        return self._mapear("SELECT * FROM reservas WHERE estado = 'Activa' ORDER BY id")
