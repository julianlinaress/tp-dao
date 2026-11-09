from biblioteca import config


def test_plazos_del_modelo_de_dominio():
    assert config.DIAS_PRESTAMO_LOCAL == 14
    assert config.DIAS_PRESTAMO_INTERBIBLIOTECARIO == 21
    assert config.DIAS_RETIRO_RESERVA == 3
    assert config.MAX_PRESTAMOS_ACTIVOS == 3
