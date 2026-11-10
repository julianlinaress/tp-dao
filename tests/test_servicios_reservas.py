import pytest

from biblioteca.dominio.enums import EstadoFisico, EstadoReserva, TipoRemito
from biblioteca.dominio.errores import RegistroDuplicado, ReglaIncumplida
from biblioteca.dominio.estados_ejemplar import DISPONIBLE, PRESTADO, RESERVADO


def prestado(esc):
    prestamo = esc.s.prestamos.solicitar(esc.socio.id, esc.libro.id, esc.cba.id, esc.cba.id)
    esc.s.prestamos.retirar(prestamo.id)
    return prestamo


def reservar(esc, socio):
    return esc.s.reservas.crear(socio.id, esc.libro.id, esc.cba.id)


def estado(esc, reserva):
    return esc.s.repositorios.reservas.requerir(reserva.id).estado


def devolver(esc, prestamo):
    esc.s.prestamos.registrar_devolucion(prestamo.id, esc.cba.id, EstadoFisico.BUENO)


def test_con_ejemplares_libres_no_se_reserva(esc):
    with pytest.raises(ReglaIncumplida, match="disponibles"):
        reservar(esc, esc.socio)


def test_sede_sin_ejemplares_no_reserva(esc):
    with pytest.raises(ReglaIncumplida, match="no posee"):
        esc.s.reservas.crear(esc.socio.id, esc.libro.id, esc.ros.id)


def test_socio_inhabilitado_no_reserva(esc):
    prestado(esc)
    otro = esc.otro_socio()
    esc.s.socios.cambiar_habilitacion(otro.id, False)
    with pytest.raises(ReglaIncumplida, match="inhabilitado"):
        reservar(esc, otro)


def test_sede_de_baja_no_reserva(esc):
    prestado(esc)
    esc.forzar_baja(esc.cba)
    with pytest.raises(ReglaIncumplida, match="baja"):
        reservar(esc, esc.otro_socio())


def test_reserva_vigente_no_se_duplica(esc):
    prestado(esc)
    otro = esc.otro_socio()
    reservar(esc, otro)
    with pytest.raises(RegistroDuplicado):
        reservar(esc, otro)


def test_devolucion_activa_la_reserva_mas_antigua_y_se_retira(esc):
    prestamo = prestado(esc)
    primero = reservar(esc, esc.otro_socio())
    segundo = reservar(esc, esc.otro_socio("30000003"))

    devolver(esc, prestamo)

    assert estado(esc, primero) is EstadoReserva.ACTIVA
    assert estado(esc, segundo) is EstadoReserva.PENDIENTE
    assert esc.estado_ejemplar() == RESERVADO

    nuevo = esc.s.reservas.retirar(primero.id)
    assert nuevo.tipo.nombre == "Local"
    assert estado(esc, primero) is EstadoReserva.ATENDIDA
    assert esc.estado_ejemplar() == PRESTADO


def test_vencimiento_automatico_pasa_a_la_siguiente(esc):
    prestamo = prestado(esc)
    primero = reservar(esc, esc.otro_socio())
    segundo = reservar(esc, esc.otro_socio("30000003"))
    devolver(esc, prestamo)

    esc.reloj.avanzar(days=3)
    assert esc.s.reservas.vencer_vencidas() == 0
    esc.reloj.avanzar(days=1)
    assert esc.s.reservas.vencer_vencidas() == 1

    assert estado(esc, primero) is EstadoReserva.VENCIDA
    assert estado(esc, segundo) is EstadoReserva.ACTIVA
    assert esc.estado_ejemplar() == RESERVADO


def test_reserva_vencida_no_se_retira(esc):
    prestamo = prestado(esc)
    reserva = reservar(esc, esc.otro_socio())
    devolver(esc, prestamo)
    esc.reloj.avanzar(days=4)
    with pytest.raises(ReglaIncumplida, match="vencida"):
        esc.s.reservas.retirar(reserva.id)


def test_cancelar_reserva_activa_libera_el_ejemplar(esc):
    prestamo = prestado(esc)
    reserva = reservar(esc, esc.otro_socio())
    devolver(esc, prestamo)
    esc.s.reservas.cancelar(reserva.id)
    assert estado(esc, reserva) is EstadoReserva.CANCELADA
    assert esc.estado_ejemplar() == DISPONIBLE


def test_retorno_de_ejemplar_activa_reserva_en_sede_propia(esc):
    prestamo = esc.s.prestamos.solicitar(esc.socio.id, esc.libro.id, esc.cba.id, esc.ros.id)
    logistica = esc.s.logistica

    def enviar(tipo):
        remito = logistica.generar_remito(tipo, [prestamo.id])
        logistica.empaquetar(remito.id)
        logistica.despachar(remito.id)
        logistica.recibir(remito.id)

    enviar(TipoRemito.IDA)
    esc.s.prestamos.retirar(prestamo.id)
    reserva = reservar(esc, esc.otro_socio())
    esc.s.prestamos.registrar_devolucion(prestamo.id, esc.ros.id, EstadoFisico.BUENO)
    assert estado(esc, reserva) is EstadoReserva.PENDIENTE

    enviar(TipoRemito.RETORNO)
    assert estado(esc, reserva) is EstadoReserva.ACTIVA


def test_no_se_da_de_baja_sede_con_reserva_vigente(esc):
    prestamo = prestado(esc)
    reserva = reservar(esc, esc.otro_socio())
    devolver(esc, prestamo)
    with pytest.raises(ReglaIncumplida, match="reserva"):
        esc.s.sedes.dar_baja(esc.cba.id)
    esc.s.reservas.cancelar(reserva.id)
    esc.s.sedes.dar_baja(esc.cba.id)

