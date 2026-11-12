from datetime import timedelta

import pytest

from biblioteca.config import MONTO_MULTA_POR_DIA, TOPE_MULTA
from biblioteca.dominio.enums import EstadoFisico, EstadoPrestamo, EstadoReserva
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.estados_ejemplar import DISPONIBLE, RESERVADO
from biblioteca.dominio.estrategias_multa import MultaFijaPorDia, MultaPorDiaConTope
from biblioteca.dominio.reserva import Reserva
from biblioteca.dominio.tipo_prestamo import INTERBIBLIOTECARIO, LOCAL
from fabrica import HOY, ejemplar, libro, prestamo_inter, sede, socio

def activo():
    prestamo = prestamo_inter()
    prestamo.ejemplar.ubicacion_actual = prestamo.sede_destino
    prestamo.retirar(HOY)
    return prestamo


def test_estrategias_de_multa():
    assert MultaFijaPorDia(100).calcular(3) == 300
    assert MultaPorDiaConTope(100, 250).calcular(3) == 250


def test_solo_el_interbibliotecario_tiene_tope_de_multa():
    assert LOCAL.estrategia_multa.calcular(100) == 100 * MONTO_MULTA_POR_DIA
    assert INTERBIBLIOTECARIO.estrategia_multa.calcular(100) == TOPE_MULTA


def test_devolucion_muy_atrasada_se_topa_en_interbibliotecario():
    prestamo = activo()
    fecha = prestamo.fecha_vencimiento + timedelta(days=100)
    prestamo.registrar_devolucion(prestamo.sede_destino, fecha, EstadoFisico.BUENO, "")
    assert prestamo.multa.monto == TOPE_MULTA


def test_retiro_calcula_vencimiento_segun_tipo():
    assert activo().fecha_vencimiento == HOY + timedelta(days=21)


def test_no_se_retira_si_no_llego_a_destino():
    with pytest.raises(ReglaIncumplida):
        prestamo_inter().retirar(HOY)


def test_devolucion_en_termino_no_genera_multa():
    prestamo = activo()
    prestamo.registrar_devolucion(prestamo.sede_destino, prestamo.fecha_vencimiento, EstadoFisico.BUENO, "")
    assert prestamo.estado is EstadoPrestamo.DEVUELTO
    assert prestamo.multa is None


def test_devolucion_atrasada_genera_multa_con_la_estrategia():
    prestamo = activo()
    fecha = prestamo.fecha_vencimiento + timedelta(days=4)
    assert prestamo.esta_vencido(fecha)
    prestamo.registrar_devolucion(prestamo.sede_destino, fecha, EstadoFisico.BUENO, "")
    assert (prestamo.multa.dias_atraso, prestamo.multa.monto) == (4, 2000)
    assert not prestamo.esta_vencido(fecha)


def test_devolucion_en_otra_sede_se_rechaza():
    prestamo = activo()
    with pytest.raises(ReglaIncumplida):
        prestamo.registrar_devolucion(prestamo.sede_origen, HOY, EstadoFisico.BUENO, "")


def test_multa_no_se_paga_dos_veces():
    prestamo = activo()
    prestamo.registrar_devolucion(prestamo.sede_destino, prestamo.fecha_vencimiento + timedelta(days=1), EstadoFisico.BUENO, "")
    prestamo.multa.pagar()
    with pytest.raises(ReglaIncumplida):
        prestamo.multa.pagar()


def test_prestamo_retirado_no_se_cancela():
    with pytest.raises(ReglaIncumplida):
        activo().cancelar()


def nueva_reserva():
    return Reserva(socio=socio(), libro=libro(), sede=sede(), fecha=HOY)


def test_reserva_activada_vence_y_libera():
    reserva = nueva_reserva()
    item = ejemplar()
    reserva.activar(item, HOY)
    assert item.estado_circulacion.nombre == RESERVADO
    assert not reserva.esta_vencida(HOY + timedelta(days=3))
    assert reserva.esta_vencida(HOY + timedelta(days=4))

    reserva.vencer()
    assert reserva.estado is EstadoReserva.VENCIDA
    assert item.estado_circulacion.nombre == DISPONIBLE


def test_reserva_pendiente_se_cancela_y_no_vence():
    reserva = nueva_reserva()
    assert not reserva.esta_vencida(HOY + timedelta(days=30))
    reserva.cancelar()
    assert reserva.estado is EstadoReserva.CANCELADA
