from datetime import date

import pytest

from biblioteca.contenedor import Servicios
from biblioteca.datos_ejemplo import CargaEjemplo
from biblioteca.dominio.enums import EstadoFisico, EstadoRecepcion, TipoRemito
from biblioteca.reportes.exportadores import exportar_csv, exportar_pdf
from biblioteca.reportes.modelo import FiltroReporte


def reporte(esc, nombre, **filtro):
    tipo = next(r for r in esc.s.reportes.listar() if type(r).__name__ == nombre)
    return tipo.generar(FiltroReporte(**filtro))


def enviar(esc, prestamo, tipo=TipoRemito.IDA, recepciones=None, horas=10, recibir=True):
    logistica = esc.s.logistica
    remito = logistica.generar_remito(tipo, [prestamo.id])
    logistica.empaquetar(remito.id)
    logistica.despachar(remito.id)
    esc.reloj.avanzar(hours=horas)
    if recibir:
        logistica.recibir(remito.id, recepciones)
    return remito


def inter(esc, socio=None, libro=None):
    return esc.s.prestamos.solicitar((socio or esc.socio).id, (libro or esc.libro).id, esc.cba.id, esc.ros.id)


def test_activos_y_en_transito(esc):
    enviar(esc, inter(esc), recibir=False)
    libro, _ = esc.otro_libro()
    local = esc.s.prestamos.solicitar(esc.socio.id, libro.id, esc.cba.id, esc.cba.id)
    esc.s.prestamos.retirar(local.id)

    resultado = reporte(esc, "PrestamosActivosYEnTransito")
    assert resultado.metricas == {"Préstamos activos": "1", "Ejemplares en tránsito": "1"}
    assert reporte(esc, "PrestamosActivosYEnTransito", tipo_prestamo="Local").metricas["Ejemplares en tránsito"] == "0"


def test_vencidos_y_multas_acumula_por_socio(esc):
    prestamo = esc.s.prestamos.solicitar(esc.socio.id, esc.libro.id, esc.cba.id, esc.cba.id)
    esc.s.prestamos.retirar(prestamo.id)
    esc.reloj.avanzar(days=17)
    esc.s.prestamos.registrar_devolucion(prestamo.id, esc.cba.id, EstadoFisico.BUENO)

    otro = esc.otro_socio()
    libro, _ = esc.otro_libro()
    vencido = esc.s.prestamos.solicitar(otro.id, libro.id, esc.cba.id, esc.cba.id)
    esc.s.prestamos.retirar(vencido.id)
    esc.reloj.avanzar(days=20)

    resultado = reporte(esc, "VencidosYMultas")
    por_dni = {f[0]: f for f in resultado.filas}
    assert por_dni["30000001"][2:] == (0, 3, 1, 1500.0, 1500.0)
    assert por_dni["30000002"][2:] == (1, 6, 0, 0, 0)
    assert resultado.metricas["Préstamos vencidos"] == "1"


def test_libros_mas_solicitados_con_filtros_y_limite(esc):
    inter(esc)
    libro, _ = esc.otro_libro()
    inter(esc, libro=libro)

    resultado = reporte(esc, "LibrosMasSolicitados")
    assert sum(f[3] for f in resultado.filas) == 2
    assert [f[5] for f in resultado.filas] == [50.0, 50.0]
    assert len(reporte(esc, "LibrosMasSolicitados", limite=1).filas) == 1
    assert [f[0] for f in reporte(esc, "LibrosMasSolicitados", genero="Novela").filas] == ["Rayuela"]
    assert reporte(esc, "LibrosMasSolicitados", desde=date(2027, 1, 1)).filas == []


def test_disponibilidad_por_sede(esc):
    esc.s.catalogo.crear_ejemplar(esc.libro.id, esc.cba.id, "A-2")
    inter(esc)
    resultado = reporte(esc, "DisponibilidadPorSede", sede_id=esc.cba.id)
    assert resultado.filas == [("Sede CBA", "Rayuela", 2, 1, 1, 0, 0, 0)]
    assert resultado.grafico.valores == [50.0]


def test_tasa_de_envios_con_incidencias(esc):
    enviar(esc, inter(esc), recepciones={esc.ejemplar.id: (EstadoRecepcion.EXTRAVIADO, "")})
    libro, _ = esc.otro_libro()
    enviar(esc, inter(esc, libro=libro))

    resultado = reporte(esc, "TasaDeEnvios")
    assert resultado.filas == [("Sede CBA", 2, 2, 1, 0, 0, 1, 50.0)]
    assert resultado.metricas["Incidencias"] == "1"
    assert reporte(esc, "TasaDeEnvios", tipo_remito="Retorno").filas == []


def test_movimiento_promedia_tiempo_de_transito(esc):
    enviar(esc, inter(esc), horas=10)
    libro, _ = esc.otro_libro()
    enviar(esc, inter(esc, libro=libro), horas=20)
    tercero, _ = esc.otro_libro("9789500000003", codigo="B-2")
    enviar(esc, inter(esc, libro=tercero), recibir=False)

    resultado = reporte(esc, "MovimientoEntreSedes")
    assert resultado.filas == [("Sede CBA", "Sede ROS", "Ida", 2, 2, 15.0)]
    assert resultado.metricas["Tránsito promedio"] == "15.0 h"


@pytest.fixture(scope="module")
def con_ejemplo(tmp_path_factory):
    ruta = tmp_path_factory.mktemp("demo") / "demo.db"
    assert CargaEjemplo(ruta).ejecutar() is True
    return ruta


def test_datos_de_ejemplo_no_se_cargan_dos_veces(con_ejemplo):
    assert CargaEjemplo(con_ejemplo).ejecutar() is False


def test_todos_los_reportes_tienen_datos_y_se_exportan(con_ejemplo, tmp_path):
    servicios = Servicios(con_ejemplo)
    reportes = servicios.reportes.listar()
    assert len(reportes) == 6
    for i, item in enumerate(reportes):
        resultado = item.generar(FiltroReporte())
        assert resultado.filas, item.titulo
        pdf, csv_ = tmp_path / f"{i}.pdf", tmp_path / f"{i}.csv"
        exportar_pdf(resultado, pdf)
        exportar_csv(resultado, csv_)
        assert pdf.read_bytes().startswith(b"%PDF")
        assert len(csv_.read_text(encoding="utf-8-sig").splitlines()) == len(resultado.filas) + 1


def test_reporte_vacio_se_exporta(esc, tmp_path):
    exportar_pdf(reporte(esc, "TasaDeEnvios"), tmp_path / "v.pdf")
