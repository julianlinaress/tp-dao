import os
import tkinter as tk
from tkinter import messagebox

import pytest

from biblioteca.contenedor import Servicios
from biblioteca.datos_ejemplo import CargaEjemplo
from biblioteca.dominio.enums import EstadoFisico, EstadoRecepcion
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.ui import componentes
from biblioteca.ui.aplicacion import Aplicacion
from biblioteca.ui.componentes import Dialogo
from biblioteca.ui.pantallas import logistica as pantalla_logistica
from biblioteca.ui.pantallas.reportes import leer_cantidad, leer_fecha

pytestmark = pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="requiere display")


@pytest.fixture
def app(tmp_path, monkeypatch):
    errores = []
    monkeypatch.setattr(componentes.messagebox, "showerror", lambda _t, m, **k: errores.append(m))
    monkeypatch.setattr(messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)
    ruta = tmp_path / "ui.db"
    CargaEjemplo(ruta).ejecutar()
    try:
        ventana = Aplicacion(Servicios(ruta), ruta)
    except tk.TclError:
        pytest.skip("Tk no disponible")
    ventana.errores = errores
    ventana.update()
    yield ventana
    ventana.destroy()


def pantalla(app, nombre):
    return next(p for p in app.pantallas if type(p).__name__ == nombre)


def responder(monkeypatch, datos):
    monkeypatch.setattr(Dialogo, "pedir", classmethod(lambda cls, *a, **k: datos))


def test_todas_las_pantallas_cargan_datos(app):
    for indice in range(len(app.pantallas)):
        app.mostrar(indice)
        app.update()
    assert app.errores == []
    assert pantalla(app, "PantallaSedes").tabla.filas()
    assert pantalla(app, "PantallaPrestamos").tabla.filas()


def test_accion_sin_seleccion_muestra_error(app):
    p = pantalla(app, "PantallaPrestamos")
    p.retirar()
    assert app.errores == ["Seleccione un registro de la tabla"]


def test_alta_de_sede_y_duplicado(app, monkeypatch):
    p = pantalla(app, "PantallaSedes")
    datos = dict(codigo="SLA", nombre="Salta", direccion="d", telefono="1", email="a@b.co", horarios="h")
    responder(monkeypatch, datos)
    p.refrescar()
    antes = len(p.tabla.filas())
    p.nueva()
    assert len(p.tabla.filas()) == antes + 1
    p.nueva()
    assert app.errores == ["Ya existe una sede con ese código"]


def test_solicitud_y_devolucion_desde_la_pantalla(app, monkeypatch):
    s = app.pantallas[0].s
    socio = s.socios.crear(dni="40000000", nombre="Nuevo", apellido="Socio", email="n@b.co")
    cba = next(x for x in s.sedes.listar() if x.codigo == "CBA")
    libro = next(x for x in s.catalogo.listar_libros() if x.titulo == "El túnel")
    p = pantalla(app, "PantallaPrestamos")
    responder(monkeypatch, {"socio": socio.id, "libro": libro.id, "origen": cba.id, "destino": cba.id})
    p.refrescar()
    p.nueva()
    assert app.errores == []
    prestamo_id = int(p.tabla.filas()[0][0])
    p.tabla.seleccionar([prestamo_id])
    p.retirar()
    p.tabla.seleccionar([prestamo_id])
    responder(monkeypatch, {"sede": cba.id, "fisico": EstadoFisico.BUENO, "observaciones": ""})
    p.devolver()
    assert app.errores == []
    assert p.tabla.filas()[0][-1] == "Devuelto"


def test_recepcion_y_trazabilidad_del_remito(app, monkeypatch):
    p = pantalla(app, "PantallaLogistica")
    p.refrescar()
    fila = next(f for f in p.remitos.filas() if f[-1] == "EnTransito")
    remito_id = int(fila[0])
    remito = p.s.logistica.obtener(remito_id)
    ejemplar = remito.detalles[0].ejemplar.id
    p.remitos.seleccionar([remito_id])
    responder(monkeypatch, {f"estado_{ejemplar}": EstadoRecepcion.DANADO, f"obs_{ejemplar}": "golpe"})
    p.recibir()
    assert app.errores == []
    assert p.s.logistica.obtener(remito_id).estado.nombre == "ConIncidencia"

    capturado = {}
    monkeypatch.setattr(pantalla_logistica, "mostrar_texto", lambda _p, _t, c: capturado.update(texto=c))
    p.remitos.seleccionar([remito_id])
    p.trazabilidad()
    assert "EnTransito -> ConIncidencia" in capturado["texto"]
    assert "golpe" in capturado["texto"]


def test_dialogo_devuelve_valores(app):
    dialogo = Dialogo(app, "Prueba", [componentes.Campo("a", "A", "x"), componentes.Campo("b", "B", 2, [("uno", 1), ("dos", 2)])])
    dialogo._aceptar()
    assert dialogo.resultado == {"a": "x", "b": 2}


def test_todos_los_reportes_se_generan(app):
    p = pantalla(app, "PantallaReportes")
    p.refrescar()
    for indice in range(len(p.s.reportes.listar())):
        p.reporte.current(indice)
        p._ajustar_filtros()
        p.generar()
        assert p.tabla.filas(), p.resultado.titulo
    assert app.errores == []


def test_fecha_invalida_en_reporte(app):
    assert leer_fecha("") is None
    with pytest.raises(ReglaIncumplida):
        leer_fecha("ayer")


def test_cantidad_invalida_en_reporte(app):
    assert leer_cantidad("") == 10
    assert leer_cantidad(" 5 ") == 5
    for texto in ("abc", "0", "-3", "2.5"):
        with pytest.raises(ReglaIncumplida):
            leer_cantidad(texto)
