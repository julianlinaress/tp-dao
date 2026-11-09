from biblioteca.reportes.modelo import Reporte, grafico_desde, sumar_por


class DisponibilidadPorSede(Reporte):
    titulo = "Disponibilidad de catálogo por sede"
    columnas = ["Sede", "Libro", "Total", "Disponibles", "Reservados", "Prestados", "En movimiento", "Fuera de servicio"]
    filtros = {"sede", "genero"}

    def _datos(self, filtro):
        return self._dao.disponibilidad_por_sede(filtro.parametros())

    def _metricas(self, filas):
        total = sum(f[2] for f in filas)
        disponibles = sum(f[3] for f in filas)
        porcentaje = disponibles * 100 / total if total else 0
        return {
            "Títulos por sede": str(len(filas)),
            "Ejemplares": str(total),
            "Disponibles": f"{disponibles} ({porcentaje:.1f} %)",
            "Fuera de servicio": str(sum(f[7] for f in filas)),
        }

    def _grafico(self, filas):
        totales = sumar_por(filas, 0, 2)
        disponibles = sumar_por(filas, 0, 3)
        porcentajes = {sede: round(disponibles[sede] * 100 / total, 1) for sede, total in totales.items()}
        return grafico_desde("Ejemplares disponibles por sede (%)", porcentajes)
