import pytest

from biblioteca.dominio.enums import EstadoFisico, EstadoPrestamo
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.estados_ejemplar import (
    DISPONIBLE,
    FUERA_DE_SERVICIO,
    PRESTADO,
    RESERVADO,
)


def local(esc, socio=None):
    return esc.s.prestamos.solicitar((socio or esc.socio).id, esc.libro.id, esc.cba.id, esc.cba.id)


def test_flujo_local_completo(esc):
    prestamo = local(esc)
    assert prestamo.tipo.nombre == "Local"
    assert esc.estado_ejemplar() == RESERVADO

    esc.s.prestamos.retirar(prestamo.id)
    assert esc.estado_ejemplar() == PRESTADO

    esc.s.prestamos.registrar_devolucion(prestamo.id, esc.cba.id, EstadoFisico.BUENO, "ok")
    assert esc.estado_ejemplar() == DISPONIBLE
    guardado = esc.s.repositorios.prestamos.requerir(prestamo.id)
    assert guardado.estado is EstadoPrestamo.DEVUELTO
    assert guardado.devolucion.observaciones == "ok"
    assert guardado.multa is None


def test_no_presta_ejemplar_no_disponible(esc):
    local(esc)
    with pytest.raises(ReglaIncumplida, match="disponibles"):
        local(esc, esc.otro_socio())


def test_no_presta_a_socio_inhabilitado(esc):
    esc.s.socios.cambiar_habilitacion(esc.socio.id, False)
    with pytest.raises(ReglaIncumplida, match="inhabilitado"):
        local(esc)


def test_no_entrega_si_se_inhabilita_antes_del_retiro(esc):
    prestamo = local(esc)
    esc.s.socios.cambiar_habilitacion(esc.socio.id, False)
    with pytest.raises(ReglaIncumplida, match="inhabilitado"):
        esc.s.prestamos.retirar(prestamo.id)


@pytest.mark.parametrize("cual", ["origen", "destino"])
def test_no_opera_con_sede_de_baja(esc, cual):
    esc.s.sedes.dar_baja((esc.cba if cual == "origen" else esc.ros).id)
    with pytest.raises(ReglaIncumplida, match="baja"):
        esc.s.prestamos.solicitar(esc.socio.id, esc.libro.id, esc.cba.id, esc.ros.id)


def test_no_presta_ejemplar_de_otra_sede(esc):
    with pytest.raises(ReglaIncumplida, match="pertenece"):
        esc.s.prestamos.solicitar(
            esc.socio.id, esc.libro.id, esc.ros.id, esc.ros.id, ejemplar_id=esc.ejemplar.id
        )


def test_maximo_de_prestamos_activos(esc):
    for i in range(3):
        libro, _ = esc.otro_libro(f"978950000001{i}", codigo=f"C-{i}")
        esc.s.prestamos.solicitar(esc.socio.id, libro.id, esc.cba.id, esc.cba.id)
    with pytest.raises(ReglaIncumplida, match="máximo"):
        local(esc)


def test_socio_con_vencidos_no_pide_otro(esc):
    libro, _ = esc.otro_libro()
    primero = local(esc)
    esc.s.prestamos.retirar(primero.id)
    esc.reloj.avanzar(days=15)
    with pytest.raises(ReglaIncumplida, match="vencidos"):
        esc.s.prestamos.solicitar(esc.socio.id, libro.id, esc.cba.id, esc.cba.id)


def test_devolucion_atrasada_registra_y_paga_multa(esc):
    prestamo = local(esc)
    esc.s.prestamos.retirar(prestamo.id)
    esc.reloj.avanzar(days=16)

    esc.s.prestamos.registrar_devolucion(prestamo.id, esc.cba.id, EstadoFisico.DETERIORADO)

    guardado = esc.s.prestamos.listar_con_multa()[0]
    assert (guardado.multa.dias_atraso, guardado.multa.monto) == (2, 1000.0)
    esc.s.prestamos.pagar_multa(guardado.multa.id)
    assert esc.s.prestamos.listar_con_multa()[0].multa.es_pagada


def test_devolucion_danada_saca_de_servicio(esc):
    prestamo = local(esc)
    esc.s.prestamos.retirar(prestamo.id)
    esc.s.prestamos.registrar_devolucion(prestamo.id, esc.cba.id, EstadoFisico.DANADO)
    assert esc.estado_ejemplar() == FUERA_DE_SERVICIO


def test_cancelar_libera_el_ejemplar(esc):
    prestamo = local(esc)
    esc.s.prestamos.cancelar(prestamo.id)
    assert esc.estado_ejemplar() == DISPONIBLE


def test_error_en_medio_no_deja_cambios_parciales(esc, monkeypatch):
    prestamo = local(esc)
    monkeypatch.setattr(
        esc.s.repositorios.ejemplares, "actualizar", lambda _: (_ for _ in ()).throw(RuntimeError)
    )
    with pytest.raises(RuntimeError):
        esc.s.prestamos.retirar(prestamo.id)
    assert esc.s.repositorios.prestamos.requerir(prestamo.id).estado is EstadoPrestamo.SOLICITADO
