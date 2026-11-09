from biblioteca.dominio.libro import Libro
from biblioteca.persistencia.dao import DAO

DUPLICADO = "Ya existe un libro con ese ISBN"


class LibroDAO(DAO[Libro]):
    tabla = "libros"
    nombre = "libro"
    orden = "titulo"

    def _desde_fila(self, fila) -> Libro:
        return Libro(
            id=fila["id"], isbn=fila["isbn"], titulo=fila["titulo"], autor=fila["autor"],
            edicion=fila["edicion"], genero=fila["genero"], editorial=fila["editorial"],
        )

    def crear(self, libro: Libro) -> Libro:
        libro.id = self._ejecutar(
            """INSERT INTO libros (isbn, titulo, autor, edicion, genero, editorial)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (libro.isbn, libro.titulo, libro.autor, libro.edicion, libro.genero, libro.editorial),
            DUPLICADO,
        )
        return libro

    def actualizar(self, libro: Libro) -> None:
        self._ejecutar(
            """UPDATE libros SET isbn = ?, titulo = ?, autor = ?, edicion = ?,
               genero = ?, editorial = ? WHERE id = ?""",
            (libro.isbn, libro.titulo, libro.autor, libro.edicion, libro.genero,
             libro.editorial, libro.id),
            DUPLICADO,
        )

    def generos(self) -> list[str]:
        filas = self._todos("SELECT DISTINCT genero FROM libros ORDER BY genero")
        return [fila["genero"] for fila in filas]
