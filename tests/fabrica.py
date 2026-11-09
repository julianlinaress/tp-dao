"""Objetos de dominio mínimos para los tests."""

from datetime import date, datetime

from biblioteca.dominio.detalle_remito import DetalleRemito
from biblioteca.dominio.ejemplar import Ejemplar
from biblioteca.dominio.enums import TipoRemito
from biblioteca.dominio.libro import Libro
from biblioteca.dominio.prestamo import SolicitudPrestamo
from biblioteca.dominio.remito import Remito
from biblioteca.dominio.sede import Sede
from biblioteca.dominio.socio import Socio
from biblioteca.dominio.tipo_prestamo import INTERBIBLIOTECARIO

HOY = date(2026, 6, 1)
AHORA = datetime(2026, 6, 1, 10, 0)


def sede(id_=1, codigo="CBA") -> Sede:
    return Sede(id=id_, codigo=codigo, nombre=codigo, direccion="d", telefono="1", email="a@b.c", horarios="h")


def socio(id_=1) -> Socio:
    return Socio(id=id_, dni=str(id_), nombre="Ana", apellido="Paz", email="a@b.c", fecha_alta=HOY)


def libro(id_=1) -> Libro:
    return Libro(id=id_, isbn="1", titulo="T", autor="A", edicion="1", genero="G", editorial="E")


def ejemplar(sede_=None, id_=1, ubicacion=None) -> Ejemplar:
    propia = sede_ or sede()
    return Ejemplar(id=id_, codigo_inventario=f"E{id_}", libro=libro(), sede=propia, ubicacion_actual=ubicacion or propia)


def prestamo_inter(origen=None, destino=None) -> SolicitudPrestamo:
    origen = origen or sede(1, "CBA")
    destino = destino or sede(2, "ROS")
    item = ejemplar(origen)
    item.reservar()
    return SolicitudPrestamo(
        socio=socio(), ejemplar=item, sede_origen=origen, sede_destino=destino,
        tipo=INTERBIBLIOTECARIO, fecha_solicitud=HOY,
    )


def remito_de(prestamo, tipo=TipoRemito.IDA) -> Remito:
    origen, destino = prestamo.sede_origen, prestamo.sede_destino
    if tipo is TipoRemito.RETORNO:
        origen, destino = destino, origen
    remito = Remito(tipo=tipo, fecha_emision=AHORA, sede_origen=origen, sede_destino=destino)
    remito.detalles.append(DetalleRemito(ejemplar=prestamo.ejemplar, prestamo=prestamo))
    return remito
