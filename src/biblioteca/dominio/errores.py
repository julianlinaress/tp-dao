"""Errores de negocio que la interfaz puede mostrar al usuario."""


class ErrorNegocio(Exception):
    pass


class TransicionInvalida(ErrorNegocio):
    pass


class ReglaIncumplida(ErrorNegocio):
    pass


class RegistroDuplicado(ErrorNegocio):
    pass


class RegistroNoEncontrado(ErrorNegocio):
    pass
