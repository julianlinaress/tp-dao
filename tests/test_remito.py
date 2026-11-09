from datetime import timedelta

import pytest

from biblioteca.dominio.enums import EstadoFisico, EstadoRecepcion, TipoRemito
from biblioteca.dominio.errores import TransicionInvalida
from biblioteca.dominio.estados_ejemplar import (
    DISPONIBLE,
    EN_TRANSITO,
    FUERA_DE_SERVICIO,
    PENDIENTE_RETORNO,
    RESERVADO,
)
from biblioteca.dominio import estados_remito as er
from fabrica import AHORA, prestamo_inter, remito_de


def en_transito():
    prestamo = prestamo_inter()
    remito = remito_de(prestamo)
    remito.empaquetar(AHORA)
    remito.despachar(AHORA + timedelta(hours=1))
    return remito, prestamo


def test_ciclo_completo_deja_historial():
    remito, prestamo = en_transito()
    assert prestamo.ejemplar.estado_circulacion.nombre == EN_TRANSITO

    llegada = AHORA + timedelta(hours=5)
    remito.recibir({}, llegada)

    assert remito.estado.nombre == er.RECIBIDO
    assert [(c.estado_anterior, c.estado_nuevo) for c in remito.cambios] == [
        (er.GENERADO, er.EMPAQUETADO),
        (er.EMPAQUETADO, er.EN_TRANSITO),
        (er.EN_TRANSITO, er.RECIBIDO),
    ]
    tramo = remito.cambios[-1]
    assert tramo.fecha_hora_fin - tramo.fecha_hora_inicio == timedelta(hours=4)
    assert prestamo.ejemplar.estado_circulacion.nombre == RESERVADO
    assert prestamo.ejemplar.ubicacion_actual == prestamo.sede_destino


@pytest.mark.parametrize(
    "recepcion,fisico,con_ubicacion",
    [
        (EstadoRecepcion.DANADO, EstadoFisico.DANADO, True),
        (EstadoRecepcion.DESTRUIDO, EstadoFisico.DESTRUIDO, True),
        (EstadoRecepcion.EXTRAVIADO, EstadoFisico.BUENO, False),
    ],
)
def test_incidencia_termina_en_con_incidencia(recepcion, fisico, con_ubicacion):
    remito, prestamo = en_transito()
    remito.recibir({prestamo.ejemplar.id: (recepcion, "nota")}, AHORA)

    assert remito.estado.nombre == er.CON_INCIDENCIA
    assert remito.tiene_incidencias()
    assert remito.detalles[0].observaciones == "nota"
    assert prestamo.ejemplar.estado_circulacion.nombre == FUERA_DE_SERVICIO
    assert prestamo.ejemplar.estado_fisico is fisico
    assert (prestamo.ejemplar.ubicacion_actual is not None) == con_ubicacion


@pytest.mark.parametrize("final", ["recibido", "incidencia", "cancelado"])
def test_estados_terminales_rechazan_todo(final):
    if final == "cancelado":
        remito = remito_de(prestamo_inter())
        remito.cancelar(AHORA)
    else:
        remito, prestamo = en_transito()
        estado = EstadoRecepcion.OK if final == "recibido" else EstadoRecepcion.DANADO
        remito.recibir({prestamo.ejemplar.id: (estado, "")}, AHORA)

    for operacion in (remito.empaquetar, remito.despachar, remito.cancelar):
        with pytest.raises(TransicionInvalida):
            operacion(AHORA)
    with pytest.raises(TransicionInvalida):
        remito.recibir({}, AHORA)
    assert not remito.esta_activo()


def test_no_se_cancela_ni_redespacha_en_transito():
    remito, _ = en_transito()
    with pytest.raises(TransicionInvalida):
        remito.cancelar(AHORA)
    with pytest.raises(TransicionInvalida):
        remito.despachar(AHORA)


def test_no_se_despacha_sin_empaquetar():
    with pytest.raises(TransicionInvalida):
        remito_de(prestamo_inter()).despachar(AHORA)


def test_remito_de_retorno_devuelve_disponible_a_su_sede():
    prestamo = prestamo_inter()
    item = prestamo.ejemplar
    item.ubicacion_actual = prestamo.sede_destino
    item.liberar()
    assert item.estado_circulacion.nombre == PENDIENTE_RETORNO

    remito = remito_de(prestamo, TipoRemito.RETORNO)
    remito.empaquetar(AHORA)
    remito.despachar(AHORA)
    remito.recibir({}, AHORA)

    assert item.estado_circulacion.nombre == DISPONIBLE
    assert item.ubicacion_actual == prestamo.sede_origen
