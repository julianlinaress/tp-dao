from biblioteca.reportes.modelo import Grafico, Reporte


class TasaDeEnvios(Reporte):
    titulo = "Tasa de envíos exitosos e incidencias"
    columnas = ["Sede origen", "Remitos", "Ejemplares", "OK", "Dañados", "Destruidos", "Extraviados", "Éxito (%)"]
    filtros = {"sede", "periodo", "tipo_remito"}

    def _datos(self, filtro):
        return self._dao.resultado_de_envios(filtro.parametros())

    def _metricas(self, filas):
        ejemplares = sum(f[2] for f in filas)
        correctos = sum(f[3] for f in filas)
        return {
            "Ejemplares recibidos": str(ejemplares),
            "Incidencias": str(ejemplares - correctos),
            "Tasa global": f"{correctos * 100 / ejemplares:.1f} %" if ejemplares else "-",
        }

    def _grafico(self, filas):
        if not filas:
            return None
        return Grafico("Tasa de éxito por sede de origen (%)", [f[0] for f in filas], [f[7] for f in filas])


class MovimientoEntreSedes(Reporte):
    titulo = "Movimiento de ejemplares entre sedes"
    columnas = ["Origen", "Destino", "Tipo", "Envíos", "Ejemplares", "Tránsito promedio (h)"]
    filtros = {"sede", "periodo", "tipo_remito"}

    def _datos(self, filtro):
        return self._dao.movimiento_entre_sedes(filtro.parametros())

    def _metricas(self, filas):
        envios = sum(f[3] for f in filas)
        horas = sum(f[3] * f[5] for f in filas)
        return {
            "Envíos recibidos": str(envios),
            "Ejemplares movidos": str(sum(f[4] for f in filas)),
            "Tránsito promedio": f"{horas / envios:.1f} h" if envios else "-",
        }

    def _grafico(self, filas):
        if not filas:
            return None
        etiquetas = [f"{f[0]} > {f[1]} ({f[2]})" for f in filas]
        return Grafico("Tránsito promedio por ruta (horas)", etiquetas, [f[5] for f in filas])
