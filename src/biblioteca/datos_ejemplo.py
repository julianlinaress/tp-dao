"""Carga de datos de ejemplo recorriendo los procesos reales del sistema."""

from datetime import timedelta
from pathlib import Path

from biblioteca.contenedor import Servicios
from biblioteca.dominio.enums import EstadoFisico, EstadoRecepcion, TipoRemito
from biblioteca.servicios.reloj import Reloj

SEDES = [("CBA", "Biblioteca Córdoba"), ("ROS", "Biblioteca Rosario"), ("MZA", "Biblioteca Mendoza"), ("TUC", "Biblioteca Tucumán")]
SOCIOS = [
    ("30111222", "Ana", "Paz"), ("31222333", "Luis", "Sosa"), ("32333444", "Marta", "Díaz"),
    ("33444555", "Pedro", "Ríos"), ("34555666", "Carla", "Vega"), ("35666777", "Tomás", "Luna"),
    ("36777888", "Sofía", "Mena"), ("37888999", "Iván", "Rojas"),
]
LIBROS = [
    ("9789500000001", "Rayuela", "Julio Cortázar", "Novela", "Sudamericana"),
    ("9789500000002", "Ficciones", "Jorge Luis Borges", "Cuento", "Emecé"),
    ("9789500000003", "El túnel", "Ernesto Sabato", "Novela", "Seix Barral"),
    ("9789500000004", "Martín Fierro", "José Hernández", "Poesía", "Losada"),
    ("9789500000005", "Facundo", "Domingo F. Sarmiento", "Ensayo", "Losada"),
    ("9789500000006", "Bestiario", "Julio Cortázar", "Cuento", "Sudamericana"),
]


class RelojEjemplo(Reloj):
    def __init__(self, dias_atras: int) -> None:
        self.momento = super().ahora().replace(microsecond=0) - timedelta(days=dias_atras)

    def ahora(self):
        return self.momento

    def avanzar(self, **delta) -> None:
        self.momento += timedelta(**delta)


class CargaEjemplo:
    def __init__(self, ruta: Path, dias_atras: int = 45) -> None:
        self.reloj = RelojEjemplo(dias_atras)
        self.s = Servicios(ruta, self.reloj)

    def ejecutar(self) -> bool:
        if self.s.sedes.listar():
            return False
        self._maestros()
        self._historia()
        return True

    def _maestros(self) -> None:
        self.sedes = {
            codigo: self.s.sedes.crear(
                codigo=codigo, nombre=nombre, direccion=f"Av. Principal {i}00", telefono=f"0351{i}00000",
                email=f"{codigo.lower()}@bibliotecas.org", horarios="Lun a Vie 8 a 20",
            )
            for i, (codigo, nombre) in enumerate(SEDES, 1)
        }
        self.socios = [
            self.s.socios.crear(dni=dni, nombre=nombre, apellido=apellido, email=f"{nombre.lower()}@correo.com")
            for dni, nombre, apellido in SOCIOS
        ]
        self.libros = [
            self.s.catalogo.crear_libro(isbn=isbn, titulo=titulo, autor=autor, edicion="1ra", genero=genero, editorial=editorial)
            for isbn, titulo, autor, genero, editorial in LIBROS
        ]
        for i, libro in enumerate(self.libros):
            for codigo in ("CBA", "ROS"):
                self.s.catalogo.crear_ejemplar(libro.id, self.sedes[codigo].id, f"{codigo}-{i + 1:03}")
        self.s.catalogo.crear_ejemplar(self.libros[0].id, self.sedes["MZA"].id, "MZA-001")

    def _inter(self, socio, libro, origen, destino):
        return self.s.prestamos.solicitar(self.socios[socio].id, self.libros[libro].id, self.sedes[origen].id, self.sedes[destino].id)

    def _enviar(self, tipo, prestamos, horas, recepciones=None):
        logistica = self.s.logistica
        remito = logistica.generar_remito(tipo, [p.id for p in prestamos])
        logistica.empaquetar(remito.id)
        self.reloj.avanzar(hours=1)
        logistica.despachar(remito.id)
        self.reloj.avanzar(hours=horas)
        if recepciones is not False:
            logistica.recibir(remito.id, recepciones)
        return remito

    def _historia(self) -> None:
        p, c = self.s.prestamos, self.sedes

        rayuela = self._inter(0, 0, "CBA", "ROS")
        ficciones = self._inter(1, 1, "CBA", "ROS")
        self._enviar(TipoRemito.IDA, [rayuela, ficciones], 20)
        p.retirar(rayuela.id)
        p.retirar(ficciones.id)
        self.reloj.avanzar(days=5)
        p.registrar_devolucion(rayuela.id, c["ROS"].id, EstadoFisico.BUENO, "Sin observaciones")
        self._enviar(TipoRemito.RETORNO, [rayuela], 26)

        tunel = self._inter(2, 2, "ROS", "MZA")
        self._enviar(TipoRemito.IDA, [tunel], 48, {self._ejemplar(tunel): (EstadoRecepcion.DANADO, "Caja mojada")})

        self.reloj.avanzar(days=20)
        p.registrar_devolucion(ficciones.id, c["ROS"].id, EstadoFisico.DETERIORADO, "Tapa gastada, entregado con atraso")
        self._enviar(TipoRemito.RETORNO, [ficciones], 24)

        fierro = p.solicitar(self.socios[3].id, self.libros[3].id, c["CBA"].id, c["CBA"].id)
        p.retirar(fierro.id)
        reserva_socio = self.socios[4]
        self.s.reservas.crear(reserva_socio.id, self.libros[3].id, c["CBA"].id)

        self.reloj.avanzar(days=8)
        facundo = self._inter(5, 4, "CBA", "ROS")
        self._enviar(TipoRemito.IDA, [facundo], 18)
        p.retirar(facundo.id)

        self.reloj.momento = Reloj().ahora().replace(microsecond=0) - timedelta(days=1)
        bestiario = self._inter(6, 5, "ROS", "CBA")
        self._enviar(TipoRemito.IDA, [bestiario], 6, recepciones=False)

        self.s.socios.cambiar_habilitacion(self.socios[7].id, False)
        self.s.sedes.dar_baja(c["TUC"].id)

    @staticmethod
    def _ejemplar(prestamo) -> int:
        return prestamo.ejemplar.id
