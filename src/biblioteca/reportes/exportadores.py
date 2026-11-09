"""Exportación de reportes a CSV y PDF."""

import csv
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from matplotlib.figure import Figure
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from biblioteca.reportes.modelo import Grafico, ResultadoReporte


def exportar_csv(resultado: ResultadoReporte, ruta: Path) -> None:
    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo, delimiter=";")
        escritor.writerow(resultado.columnas)
        escritor.writerows(resultado.filas)


def _imagen(grafico: Grafico) -> Image:
    figura = Figure(figsize=(9, 3.4))
    eje = figura.subplots()
    posiciones = list(range(len(grafico.etiquetas)))
    eje.barh(posiciones, grafico.valores, color="#2f6f8f")
    eje.set_yticks(posiciones, [etiqueta[:40] for etiqueta in grafico.etiquetas], fontsize=8)
    eje.invert_yaxis()
    eje.set_title(grafico.titulo, fontsize=11)
    eje.spines[["top", "right"]].set_visible(False)
    figura.tight_layout()

    memoria = BytesIO()
    figura.savefig(memoria, format="png", dpi=150)
    memoria.seek(0)
    return Image(memoria, width=23 * cm, height=8.7 * cm)


def _tabla(resultado: ResultadoReporte, estilos) -> Table:
    celda = estilos["BodyText"].clone("celda", fontSize=8, leading=10)
    cabecera = estilos["BodyText"].clone("cabecera", fontSize=8, leading=10, textColor=colors.white)
    datos = [[Paragraph(escape(c), cabecera) for c in resultado.columnas]]
    datos += [[Paragraph(escape(str(v)), celda) for v in fila] for fila in resultado.filas]
    tabla = Table(datos, repeatRows=1, colWidths=[26.7 * cm / len(resultado.columnas)] * len(resultado.columnas))
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f6f8f")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4f7")]),
            ]
        )
    )
    return tabla


def exportar_pdf(resultado: ResultadoReporte, ruta: Path) -> None:
    estilos = getSampleStyleSheet()
    documento = SimpleDocTemplate(
        str(ruta), pagesize=landscape(A4), leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, title=resultado.titulo,
    )
    elementos = [Paragraph(escape(resultado.titulo), estilos["Title"])]
    for nombre, valor in resultado.metricas.items():
        elementos.append(Paragraph(f"<b>{escape(nombre)}:</b> {escape(valor)}", estilos["BodyText"]))
    elementos.append(Spacer(1, 0.4 * cm))
    if resultado.grafico:
        elementos += [_imagen(resultado.grafico), Spacer(1, 0.4 * cm)]
    if resultado.filas:
        elementos.append(_tabla(resultado, estilos))
    else:
        elementos.append(Paragraph("Sin datos para los filtros elegidos.", estilos["BodyText"]))
    documento.build(elementos)
