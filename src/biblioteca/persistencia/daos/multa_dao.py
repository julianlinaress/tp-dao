from biblioteca.dominio.multa import Multa
from biblioteca.persistencia.dao import DAO


class MultaDAO(DAO[Multa]):
    tabla = "multas"
    nombre = "multa"

    def _desde_fila(self, fila) -> Multa:
        return Multa(
            id=fila["id"], dias_atraso=fila["dias_atraso"], monto=fila["monto"],
            es_pagada=bool(fila["es_pagada"]),
        )

    def crear(self, prestamo_id: int, multa: Multa) -> None:
        multa.id = self._ejecutar(
            "INSERT INTO multas (prestamo_id, dias_atraso, monto, es_pagada) VALUES (?, ?, ?, ?)",
            (prestamo_id, multa.dias_atraso, multa.monto, multa.es_pagada),
            "El préstamo ya tiene una multa registrada",
        )

    def actualizar(self, multa: Multa) -> None:
        self._ejecutar("UPDATE multas SET es_pagada = ? WHERE id = ?", (multa.es_pagada, multa.id))

    def obtener_por_prestamo(self, prestamo_id: int) -> Multa | None:
        resultado = self._mapear("SELECT * FROM multas WHERE prestamo_id = ?", (prestamo_id,))
        return resultado[0] if resultado else None
