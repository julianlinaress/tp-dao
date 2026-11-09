from biblioteca.reportes.modelo import Reporte, grafico_desde, sumar_por


class PrestamosActivosYEnTransito(Reporte):
    titulo = "Préstamos activos y material en tránsito"
    columnas = ["Categoría", "Libro", "Ejemplar", "Socio", "Origen", "Destino", "Fecha", "Referencia"]
    filtros = {"sede", "periodo", "tipo_prestamo"}

    def _datos(self, filtro):
        return self._dao.activos_y_en_transito(filtro.parametros())

    def _metricas(self, filas):
        por_categoria = sumar_por(filas, 0)
        return {
            "Préstamos activos": str(por_categoria.get("Préstamo activo", 0)),
            "Ejemplares en tránsito": str(por_categoria.get("En tránsito", 0)),
        }

    def _grafico(self, filas):
        return grafico_desde("Movimientos por sede de destino", sumar_por(filas, 5))


class VencidosYMultas(Reporte):
    titulo = "Préstamos vencidos y multas acumuladas"
    columnas = ["DNI", "Socio", "Vencidos", "Mayor atraso (días)", "Multas", "Total ($)", "Impago ($)"]
    filtros = {"sede", "periodo"}

    def _datos(self, filtro):
        parametros = filtro.parametros() | {"hoy": self._reloj.hoy().isoformat()}
        return self._dao.vencidos_y_multas(parametros)

    def _metricas(self, filas):
        return {
            "Socios afectados": str(len(filas)),
            "Préstamos vencidos": str(sum(f[2] for f in filas)),
            "Total multado": f"$ {sum(f[5] for f in filas):,.2f}",
            "Total impago": f"$ {sum(f[6] for f in filas):,.2f}",
        }

    def _grafico(self, filas):
        impagos = {f[1]: f[6] for f in filas[:10] if f[6] > 0}
        return grafico_desde("Multas impagas por socio ($)", impagos)


class LibrosMasSolicitados(Reporte):
    titulo = "Libros más solicitados entre sedes"
    columnas = ["Libro", "Autor", "Género", "Solicitudes", "Sedes destino", "Participación (%)"]
    filtros = {"sede", "periodo", "genero", "limite"}

    def _datos(self, filtro):
        return self._dao.libros_mas_solicitados(filtro.parametros())

    def _metricas(self, filas):
        return {
            "Títulos listados": str(len(filas)),
            "Solicitudes listadas": str(sum(f[3] for f in filas)),
            "Más solicitado": filas[0][0] if filas else "-",
        }

    def _grafico(self, filas):
        return grafico_desde("Solicitudes interbibliotecarias", {f[0]: f[3] for f in filas})
