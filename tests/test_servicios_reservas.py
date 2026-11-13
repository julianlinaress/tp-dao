import pytest

from biblioteca.dominio.enums import EstadoFisico, EstadoReserva, TipoRemito
from biblioteca.dominio.errores import RegistroDuplicado, ReglaIncumplida
from biblioteca.dominio.estados_ejemplar import DISPONIBLE, FUERA_DE_SERVICIO, PRESTADO, RESERVADO


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


@pytest.mark.parametrize("fisico", [EstadoFisico.BUENO, EstadoFisico.DETERIORADO])
def test_alta_de_ejemplar_activa_la_reserva_mas_antigua(esc, fisico):
    prestado(esc)
    primera = reservar(esc, esc.otro_socio())
    esc.reloj.avanzar(days=1)
    segunda = reservar(esc, esc.otro_socio("30000003"))

    ejemplar = esc.s.catalogo.crear_ejemplar(esc.libro.id, esc.cba.id, "A-2", fisico)

    guardada = esc.s.repositorios.reservas.requerir(primera.id)
    assert guardada.estado is EstadoReserva.ACTIVA
    assert guardada.ejemplar.id == ejemplar.id
    assert guardada.fecha_vencimiento > esc.reloj.hoy()
    assert estado(esc, segunda) is EstadoReserva.PENDIENTE
    assert ejemplar.estado_circulacion.nombre == RESERVADO
    assert esc.estado_ejemplar(ejemplar) == RESERVADO


@pytest.mark.parametrize("fisico", [EstadoFisico.DANADO, EstadoFisico.DESTRUIDO])
def test_alta_fuera_de_servicio_no_activa_reservas(esc, fisico):
    prestado(esc)
    reserva = reservar(esc, esc.otro_socio())

    ejemplar = esc.s.catalogo.crear_ejemplar(esc.libro.id, esc.cba.id, "A-2", fisico)

    assert estado(esc, reserva) is EstadoReserva.PENDIENTE
    assert esc.estado_ejemplar(ejemplar) == FUERA_DE_SERVICIO


@pytest.mark.parametrize("otra_sede", [False, True])
def test_alta_no_activa_reservas_de_otro_libro_o_sede(esc, otra_sede):
    prestado(esc)
    reserva = reservar(esc, esc.otro_socio())

    if otra_sede:
        ejemplar = esc.s.catalogo.crear_ejemplar(esc.libro.id, esc.ros.id, "A-2")
    else:
        _, ejemplar = esc.otro_libro()

    assert estado(esc, reserva) is EstadoReserva.PENDIENTE
    assert esc.estado_ejemplar(ejemplar) == DISPONIBLE


def test_error_al_activar_reserva_revierte_alta_de_ejemplar(esc, monkeypatch):
    prestado(esc)
    reserva = reservar(esc, esc.otro_socio())
    actualizar = esc.s.repositorios.reservas.actualizar

    def actualizar_y_fallar(reserva):
        actualizar(reserva)
        raise RuntimeError("Fallo al activar reserva")

    monkeypatch.setattr(esc.s.repositorios.reservas, "actualizar", actualizar_y_fallar)

    with pytest.raises(RuntimeError, match="Fallo al activar reserva"):
        esc.s.catalogo.crear_ejemplar(esc.libro.id, esc.cba.id, "A-2")

    assert [e.id for e in esc.s.catalogo.listar_ejemplares()] == [esc.ejemplar.id]
    guardada = esc.s.repositorios.reservas.requerir(reserva.id)
    assert guardada.estado is EstadoReserva.PENDIENTE
    assert guardada.ejemplar is None
    assert guardada.fecha_vencimiento is None
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


def test_retiro_de_reserva_exige_socio_sin_vencidos(esc):
    otro = esc.otro_socio()
    libro, _ = esc.otro_libro()
    vencido = esc.s.prestamos.solicitar(otro.id, libro.id, esc.cba.id, esc.cba.id)
    esc.s.prestamos.retirar(vencido.id)
    prestamo = prestado(esc)
    reserva = reservar(esc, otro)
    esc.reloj.avanzar(days=15)
    devolver(esc, prestamo)
    with pytest.raises(ReglaIncumplida, match="vencidos"):
        esc.s.reservas.retirar(reserva.id)


def test_retiro_de_reserva_informa_socio_inhabilitado(esc):
    prestamo = prestado(esc)
    otro = esc.otro_socio()
    reserva = reservar(esc, otro)
    devolver(esc, prestamo)
    esc.s.socios.cambiar_habilitacion(otro.id, False)
    with pytest.raises(ReglaIncumplida, match="inhabilitado"):
        esc.s.reservas.retirar(reserva.id)
