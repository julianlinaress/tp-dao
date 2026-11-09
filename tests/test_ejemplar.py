import pytest

from biblioteca.dominio.enums import EstadoFisico
from biblioteca.dominio.errores import ReglaIncumplida, TransicionInvalida
from biblioteca.dominio.estados_ejemplar import (
    DISPONIBLE,
    EN_TRANSITO,
    FUERA_DE_SERVICIO,
    PENDIENTE_RETORNO,
    PRESTADO,
    RESERVADO,
)
from fabrica import ejemplar, sede


def nombre(item):
    return item.estado_circulacion.nombre


def llevar_a(destino):
    item = ejemplar()
    if destino == RESERVADO:
        item.reservar()
    elif destino == PRESTADO:
        item.prestar()
    elif destino == EN_TRANSITO:
        item.enviar()
    elif destino == FUERA_DE_SERVICIO:
        item.sacar_de_servicio()
    elif destino == PENDIENTE_RETORNO:
        item.ubicacion_actual = sede(2, "ROS")
        item.quedar_libre()
    return item


@pytest.mark.parametrize(
    "estado,operacion",
    [
        (DISPONIBLE, lambda e: e.devolver(EstadoFisico.BUENO)),
        (DISPONIBLE, lambda e: e.recibir(sede())),
        (DISPONIBLE, lambda e: e.reparar()),
        (RESERVADO, lambda e: e.reservar()),
        (PRESTADO, lambda e: e.prestar()),
        (PRESTADO, lambda e: e.enviar()),
        (EN_TRANSITO, lambda e: e.prestar()),
        (EN_TRANSITO, lambda e: e.enviar()),
        (PENDIENTE_RETORNO, lambda e: e.prestar()),
        (PENDIENTE_RETORNO, lambda e: e.reservar()),
        (FUERA_DE_SERVICIO, lambda e: e.prestar()),
        (FUERA_DE_SERVICIO, lambda e: e.sacar_de_servicio()),
    ],
)
def test_operaciones_rechazadas(estado, operacion):
    with pytest.raises(TransicionInvalida):
        operacion(llevar_a(estado))


@pytest.mark.parametrize(
    "fisico,esperado",
    [
        (EstadoFisico.BUENO, DISPONIBLE),
        (EstadoFisico.DETERIORADO, DISPONIBLE),
        (EstadoFisico.DANADO, FUERA_DE_SERVICIO),
        (EstadoFisico.DESTRUIDO, FUERA_DE_SERVICIO),
    ],
)
def test_devolucion_segun_estado_fisico(fisico, esperado):
    item = llevar_a(PRESTADO)
    item.devolver(fisico)
    assert nombre(item) == esperado
    assert item.estado_fisico is fisico


def test_devuelto_en_sede_ajena_queda_pendiente_de_retorno():
    item = llevar_a(PRESTADO)
    item.ubicacion_actual = sede(2, "ROS")
    item.devolver(EstadoFisico.BUENO)
    assert nombre(item) == PENDIENTE_RETORNO
    assert not item.puede_entregarse()


def test_envio_vacia_ubicacion_y_recepcion_apartada_queda_reservado():
    item = llevar_a(RESERVADO)
    item.enviar()
    assert item.ubicacion_actual is None
    destino = sede(2, "ROS")
    item.recibir(destino, apartado=True)
    assert nombre(item) == RESERVADO
    assert item.ubicacion_actual == destino


def test_retorno_a_sede_propia_queda_disponible():
    item = llevar_a(PENDIENTE_RETORNO)
    item.enviar()
    item.recibir(item.sede)
    assert nombre(item) == DISPONIBLE


def test_liberar_en_sede_ajena_queda_pendiente_de_retorno():
    item = llevar_a(RESERVADO)
    item.ubicacion_actual = sede(2, "ROS")
    item.liberar()
    assert nombre(item) == PENDIENTE_RETORNO


def test_reparar_restaura_estado_fisico():
    item = llevar_a(PRESTADO)
    item.devolver(EstadoFisico.DANADO)
    item.reparar()
    assert nombre(item) == DISPONIBLE
    assert item.estado_fisico is EstadoFisico.BUENO


def test_destruido_no_se_repara():
    item = llevar_a(PRESTADO)
    item.devolver(EstadoFisico.DESTRUIDO)
    with pytest.raises(ReglaIncumplida):
        item.reparar()
