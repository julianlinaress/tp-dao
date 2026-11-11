import pytest

from biblioteca.dominio.enums import EstadoFisico
from biblioteca.dominio.errores import (
    RegistroDuplicado,
    RegistroNoEncontrado,
    ReglaIncumplida,
)
from biblioteca.dominio.estados_ejemplar import DISPONIBLE, FUERA_DE_SERVICIO


def test_duplicados_rechazados(esc):
    s = esc.s
    with pytest.raises(RegistroDuplicado):
        s.sedes.crear(codigo="cba", nombre="x", direccion="x", telefono="1", email="a@b.co", horarios="x")
    with pytest.raises(RegistroDuplicado):
        s.socios.crear(dni="30000001", nombre="x", apellido="y", email="a@b.co")
    with pytest.raises(RegistroDuplicado):
        s.catalogo.crear_libro(isbn="9789500000001", titulo="x", autor="x", edicion="1", genero="x", editorial="x")
    with pytest.raises(RegistroDuplicado):
        s.catalogo.crear_ejemplar(esc.libro.id, esc.cba.id, "A-1")


def test_datos_invalidos(esc):
    with pytest.raises(ReglaIncumplida):
        esc.s.socios.crear(dni="abc", nombre="x", apellido="y", email="a@b.co")
    with pytest.raises(ReglaIncumplida):
        esc.s.socios.crear(dni="30000009", nombre=" ", apellido="y", email="a@b.co")
    with pytest.raises(ReglaIncumplida):
        esc.s.socios.crear(dni="30000009", nombre="x", apellido="y", email="malo")
    with pytest.raises(ReglaIncumplida):
        esc.s.catalogo.crear_libro(isbn="12", titulo="x", autor="x", edicion="1", genero="x", editorial="x")


def test_isbn_se_normaliza_y_conserva_texto(esc):
    assert esc.libro.isbn == "9789500000001"
    con_x = esc.s.catalogo.crear_libro(isbn="0-19-853453-X", titulo="x", autor="x", edicion="1", genero="x", editorial="x")
    assert esc.s.repositorios.libros.requerir(con_x.id).isbn == "019853453X"


def test_baja_logica_conserva_la_sede(esc):
    esc.s.sedes.dar_baja(esc.ros.id)
    assert not esc.s.repositorios.sedes.requerir(esc.ros.id).es_activa
    assert esc.ros in esc.s.sedes.listar()
    assert esc.ros not in esc.s.sedes.listar_activas()


def test_modificacion_y_busqueda_de_socio(esc):
    esc.s.socios.actualizar(esc.socio.id, dni="30000001", nombre="Ana", apellido="Ruiz", email="a@b.co")
    assert [x.apellido for x in esc.s.socios.listar("ruiz")] == ["Ruiz"]


def test_registro_inexistente(esc):
    with pytest.raises(RegistroNoEncontrado):
        esc.s.sedes.dar_baja(999)


def test_sacar_de_servicio_y_reparar(esc):
    esc.s.catalogo.sacar_de_servicio(esc.ejemplar.id, EstadoFisico.DANADO)
    assert esc.estado_ejemplar() == FUERA_DE_SERVICIO
    esc.s.catalogo.reparar(esc.ejemplar.id)
    assert esc.estado_ejemplar() == DISPONIBLE


def test_disponibilidad_por_libro_y_sede(esc):
    esc.s.catalogo.crear_ejemplar(esc.libro.id, esc.ros.id, "A-2")
    esc.s.prestamos.solicitar(esc.socio.id, esc.libro.id, esc.cba.id, esc.cba.id)

    filas = esc.s.catalogo.disponibilidad(libro_id=esc.libro.id)
    assert {(f["sede"], f["total"], f["disponibles"]) for f in filas} == {
        ("Sede CBA", 1, 0),
        ("Sede ROS", 1, 1),
    }
    assert len(esc.s.catalogo.disponibilidad(sede_id=esc.ros.id)) == 1


def test_no_se_da_de_baja_sede_con_prestamo_sin_cerrar(esc):
    esc.s.prestamos.solicitar(esc.socio.id, esc.libro.id, esc.cba.id, esc.cba.id)
    with pytest.raises(ReglaIncumplida, match="préstamo"):
        esc.s.sedes.dar_baja(esc.cba.id)
    assert esc.s.repositorios.sedes.requerir(esc.cba.id).es_activa


@pytest.mark.parametrize("fisico", [EstadoFisico.DANADO, EstadoFisico.DESTRUIDO])
def test_alta_de_ejemplar_danado_queda_fuera_de_servicio(esc, fisico):
    ejemplar = esc.s.catalogo.crear_ejemplar(esc.libro.id, esc.cba.id, "D-1", fisico)
    assert esc.estado_ejemplar(ejemplar) == FUERA_DE_SERVICIO
    filas = esc.s.catalogo.disponibilidad(esc.libro.id, esc.cba.id)
    assert (filas[0]["total"], filas[0]["disponibles"]) == (2, 1)


def test_alta_de_ejemplar_deteriorado_queda_disponible(esc):
    ejemplar = esc.s.catalogo.crear_ejemplar(esc.libro.id, esc.cba.id, "D-1", EstadoFisico.DETERIORADO)
    guardado = esc.s.repositorios.ejemplares.requerir(ejemplar.id)
    assert guardado.estado_circulacion.nombre == DISPONIBLE
    assert guardado.estado_fisico is EstadoFisico.DETERIORADO


def test_eliminar_registros_sin_historial(esc):
    s = esc.s
    libro = s.catalogo.crear_libro(isbn="9789500000002", titulo="Nuevo", autor="x", edicion="1", genero="x", editorial="x")
    ejemplar = s.catalogo.crear_ejemplar(libro.id, esc.cba.id, "Z-1")
    with pytest.raises(ReglaIncumplida):
        s.catalogo.eliminar_libro(libro.id)
    s.catalogo.eliminar_ejemplar(ejemplar.id)
    s.catalogo.eliminar_libro(libro.id)
    socio = s.socios.crear(dni="30000099", nombre="x", apellido="y", email="a@b.co")
    s.socios.eliminar(socio.id)
    assert libro not in s.catalogo.listar_libros()
    assert socio not in s.socios.listar()


def test_no_se_elimina_con_historial(esc):
    with pytest.raises(ReglaIncumplida, match="ejemplares"):
        esc.s.catalogo.eliminar_libro(esc.libro.id)
    esc.s.prestamos.solicitar(esc.socio.id, esc.libro.id, esc.cba.id, esc.cba.id)
    with pytest.raises(ReglaIncumplida, match="prestamos"):
        esc.s.socios.eliminar(esc.socio.id)
    with pytest.raises(ReglaIncumplida, match="prestamos"):
        esc.s.catalogo.eliminar_ejemplar(esc.ejemplar.id)


def test_reactivar_sede(esc):
    esc.s.sedes.dar_baja(esc.ros.id)
    esc.s.sedes.reactivar(esc.ros.id)
    assert esc.ros in esc.s.sedes.listar_activas()
