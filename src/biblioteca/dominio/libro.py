from dataclasses import dataclass

from biblioteca.dominio.entidad import Entidad


@dataclass(kw_only=True, eq=False)
class Libro(Entidad):
    isbn: str
    titulo: str
    autor: str
    edicion: str
    genero: str
    editorial: str

    def __str__(self) -> str:
        return f"{self.titulo} - {self.autor}"
