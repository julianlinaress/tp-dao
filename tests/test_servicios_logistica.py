import pytest

from biblioteca.dominio.enums import (
    EstadoFisico,
    EstadoPrestamo,
    EstadoRecepcion,
    TipoRemito,
)
from biblioteca.dominio.errores import ReglaIncumplida, TransicionInvalida
from biblioteca.dominio import estados_ejemplar as ee, estados_remito as er


def solicitar(esc):
    return esc.s.prestamos.solicitar(esc.socio.id, esc.libro.id, esc.cba.id, esc.ros.id)


def enviar(esc, prestamo_ids, tipo=TipoRemito.IDA):
    remito = esc.s.logistica.generar_remito(tipo, prestamo_ids)
    esc.s.logistica.empaquetar(remito.id)
    esc.s.logistica.despachar(remito.id)
    return remito


def en_destino(esc):
    prestamo = solicitar(esc)
    remito = enviar(esc, [prestamo.id])
    esc.reloj.avanzar(hours=6)
    esc.s.logistica.recibir(remito.id)
    return prestamo


def test_ciclo_interbibliotecario_completo_con_ida_y_retorno(esc):
    prestamo = en_destino(esc)
    assert esc.estado_ejemplar() == ee.RESERVADO

    esc.s.prestamos.retirar(prestamo.id)
    assert esc.estado_ejemplar() == ee.PRESTADO
    esc.s.prestamos.registrar_devolucion(prestamo.id, esc.ros.id, EstadoFisico.BUENO)
    assert esc.estado_ejemplar() == ee.PENDIENTE_RETORNO
    assert [p.id for p in esc.s.logistica.pendientes(TipoRemito.RETORNO)] == [prestamo.id]

    retorno = enviar(esc, [prestamo.id], TipoRemito.RETORNO)
    assert esc.s.logistica.pendientes(TipoRemito.RETORNO) == []
    assert retorno.sede_origen == esc.ros and retorno.sede_destino == esc.cba
    esc.s.logistica.recibir(retorno.id)

    assert esc.estado_ejemplar() == ee.DISPONIBLE
    item = esc.s.repositorios.ejemplares.requerir(esc.ejemplar.id)
    assert item.ubicacion_actual == esc.cba


def test_historial_del_remito_se_persiste(esc):
    prestamo = solicitar(esc)
    remito = enviar(esc, [prestamo.id])
    esc.reloj.avanzar(hours=6)
    esc.s.logistica.recibir(remito.id)
    guardado = esc.s.logistica.obtener(remito.id)
    assert guardado.estado.nombre == er.RECIBIDO
    assert [c.estado_nuevo for c in guardado.cambios] == [er.EMPAQUETADO, er.EN_TRANSITO, er.RECIBIDO]
    assert (guardado.cambios[-1].fecha_hora_fin - guardado.cambios[-1].fecha_hora_inicio).seconds == 21600


def test_prestamo_no_se_retira_antes_de_llegar(esc):
    prestamo = solicitar(esc)
    with pytest.raises(ReglaIncumplida, match="todavía"):
        esc.s.prestamos.retirar(prestamo.id)


def test_incidencia_en_ida_anula_el_prestamo(esc):
    prestamo = solicitar(esc)
    remito = enviar(esc, [prestamo.id])
    esc.s.logistica.recibir(
        remito.id, {esc.ejemplar.id: (EstadoRecepcion.EXTRAVIADO, "no llegó")}
    )
    guardado = esc.s.logistica.obtener(remito.id)
    assert guardado.estado.nombre == er.CON_INCIDENCIA
    assert guardado.detalles[0].observaciones == "no llegó"
    assert esc.estado_ejemplar() == ee.FUERA_DE_SERVICIO
    assert esc.s.repositorios.prestamos.requerir(prestamo.id).estado is EstadoPrestamo.CANCELADO


def test_remito_con_varios_ejemplares(esc):
    primero = solicitar(esc)
    libro, ejemplar = esc.otro_libro()
    segundo = esc.s.prestamos.solicitar(esc.socio.id, libro.id, esc.cba.id, esc.ros.id)
    remito = enviar(esc, [primero.id, segundo.id])
    esc.s.logistica.recibir(remito.id, {ejemplar.id: (EstadoRecepcion.DANADO, "")})

    assert esc.estado_ejemplar() == ee.RESERVADO
    assert esc.estado_ejemplar(ejemplar) == ee.FUERA_DE_SERVICIO
    assert esc.s.repositorios.prestamos.requerir(primero.id).estado is EstadoPrestamo.SOLICITADO
    assert esc.s.repositorios.prestamos.requerir(segundo.id).estado is EstadoPrestamo.CANCELADO


def test_remito_exige_misma_ruta(esc):
    primero = solicitar(esc)
    otra = esc.s.sedes.crear(codigo="MZA", nombre="Mendoza", direccion="c", telefono="1", email="a@b.co", horarios="h")
    libro, _ = esc.otro_libro()
    segundo = esc.s.prestamos.solicitar(esc.socio.id, libro.id, esc.cba.id, otra.id)
    with pytest.raises(ReglaIncumplida, match="compartir"):
        esc.s.logistica.generar_remito(TipoRemito.IDA, [primero.id, segundo.id])


def test_ejemplar_no_entra_en_dos_remitos_activos(esc):
    prestamo = solicitar(esc)
    esc.s.logistica.generar_remito(TipoRemito.IDA, [prestamo.id])
    assert esc.s.logistica.pendientes(TipoRemito.IDA) == []
    with pytest.raises(ReglaIncumplida):
        esc.s.logistica.generar_remito(TipoRemito.IDA, [prestamo.id])


def test_remito_cancelado_permite_generar_otro(esc):
    prestamo = solicitar(esc)
    remito = esc.s.logistica.generar_remito(TipoRemito.IDA, [prestamo.id])
    esc.s.logistica.cancelar(remito.id)
    assert [p.id for p in esc.s.logistica.pendientes(TipoRemito.IDA)] == [prestamo.id]


def test_sede_de_baja_bloquea_generar_empaquetar_y_despachar(esc):
    prestamo = solicitar(esc)
    remito = esc.s.logistica.generar_remito(TipoRemito.IDA, [prestamo.id])
    esc.forzar_baja(esc.ros)
    with pytest.raises(ReglaIncumplida, match="baja"):
        esc.s.logistica.empaquetar(remito.id)
    with pytest.raises(ReglaIncumplida, match="baja"):
        esc.s.logistica.despachar(remito.id)
    esc.s.logistica.cancelar(remito.id)
    with pytest.raises(ReglaIncumplida, match="baja"):
        esc.s.logistica.generar_remito(TipoRemito.IDA, [prestamo.id])


def test_no_se_da_de_baja_sede_con_remito_activo(esc):
    prestamo = solicitar(esc)
    esc.s.logistica.generar_remito(TipoRemito.IDA, [prestamo.id])
    with pytest.raises(ReglaIncumplida, match="remito"):
        esc.s.sedes.dar_baja(esc.ros.id)


def test_no_se_da_de_baja_sede_con_ejemplar_pendiente_de_retorno(esc):
    prestamo = en_destino(esc)
    esc.s.prestamos.retirar(prestamo.id)
    esc.s.prestamos.registrar_devolucion(prestamo.id, esc.ros.id, EstadoFisico.BUENO)
    for sede in (esc.cba, esc.ros):
        with pytest.raises(ReglaIncumplida, match="ejemplar"):
            esc.s.sedes.dar_baja(sede.id)
    retorno = enviar(esc, [prestamo.id], TipoRemito.RETORNO)
    esc.s.logistica.recibir(retorno.id)
    esc.s.sedes.dar_baja(esc.cba.id)
    assert not esc.s.repositorios.sedes.requerir(esc.cba.id).es_activa


def test_prestamo_con_remito_activo_no_se_cancela(esc):
    prestamo = solicitar(esc)
    esc.s.logistica.generar_remito(TipoRemito.IDA, [prestamo.id])
    with pytest.raises(ReglaIncumplida, match="remito"):
        esc.s.prestamos.cancelar(prestamo.id)


def test_cancelar_tras_llegada_deja_pendiente_de_retorno(esc):
    prestamo = en_destino(esc)
    esc.s.prestamos.cancelar(prestamo.id)
    assert esc.estado_ejemplar() == ee.PENDIENTE_RETORNO
    assert [p.id for p in esc.s.logistica.pendientes(TipoRemito.RETORNO)] == [prestamo.id]


def test_retorno_no_recoge_prestamos_anteriores_del_mismo_ejemplar(esc):
    primero = en_destino(esc)
    esc.s.prestamos.cancelar(primero.id)
    retorno = enviar(esc, [primero.id], TipoRemito.RETORNO)
    esc.s.logistica.recibir(retorno.id)

    segundo = en_destino(esc)
    esc.s.prestamos.cancelar(segundo.id)
    assert [p.id for p in esc.s.logistica.pendientes(TipoRemito.RETORNO)] == [segundo.id]


def test_recibir_dos_veces_se_rechaza(esc):
    prestamo = solicitar(esc)
    remito = enviar(esc, [prestamo.id])
    esc.s.logistica.recibir(remito.id)
    with pytest.raises(TransicionInvalida):
        esc.s.logistica.recibir(remito.id)
