from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from biblioteca.config import DIRECTORIO_SALIDAS
from biblioteca.dominio.enums import TipoRemito
from biblioteca.dominio.errores import ReglaIncumplida
from biblioteca.dominio.tipo_prestamo import TIPOS_PRESTAMO
from biblioteca.reportes.exportadores import exportar_csv, exportar_pdf
from biblioteca.reportes.modelo import FiltroReporte
from biblioteca.ui.componentes import Pantalla, Selector, Tabla, accion


def leer_fecha(texto: str) -> date | None:
    texto = texto.strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError as error:
        raise ReglaIncumplida("Las fechas deben tener el formato AAAA-MM-DD") from error


class PantallaReportes(Pantalla):
    def construir(self) -> None:
        self.resultado = None
        arriba = ttk.Frame(self)
        arriba.pack(fill="x", pady=(0, 6))
        ttk.Label(arriba, text="Reporte:").pack(side="left")
        self.reporte = Selector(arriba, width=48)
        self.reporte.pack(side="left", padx=6)
        self.reporte.cargar([(r.titulo, r) for r in self.s.reportes.listar()])
        self.reporte.bind("<<ComboboxSelected>>", lambda _: self._ajustar_filtros())
        for texto, comando in (("Generar", self.generar), ("Exportar PDF", self.pdf), ("Exportar CSV", self.csv)):
            ttk.Button(arriba, text=texto, command=comando).pack(side="left", padx=(0, 6))

        marco = ttk.Frame(self)
        marco.pack(fill="x", pady=(0, 6))
        self.sede = self._selector(marco, "Sede:", 22)
        self.genero = self._selector(marco, "Género:", 12)
        self.tipo_prestamo = self._selector(marco, "Préstamo:", 15)
        self.tipo_prestamo.cargar([(n, n) for n in TIPOS_PRESTAMO], vacio="Todos")
        self.tipo_remito = self._selector(marco, "Remito:", 9)
        self.tipo_remito.cargar([(t.value, t.value) for t in TipoRemito], vacio="Todos")
        self.desde = self._entrada(marco, "Desde:", 11)
        self.hasta = self._entrada(marco, "Hasta:", 11)
        self.limite = ttk.Spinbox(marco, from_=1, to=100, width=4)
        self.limite.set(10)
        ttk.Label(marco, text="Top:").pack(side="left", padx=(6, 3))
        self.limite.pack(side="left")

        self.metricas = ttk.Label(self, font=("", 10, "bold"), wraplength=1150, justify="left")
        self.metricas.pack(fill="x", pady=6)
        self.tabla = Tabla(self, [("Resultado", 400)])
        self.tabla.pack(fill="both", expand=True)
        self._ajustar_filtros()

    @staticmethod
    def _selector(padre, etiqueta: str, ancho: int) -> Selector:
        ttk.Label(padre, text=etiqueta).pack(side="left", padx=(6, 3))
        selector = Selector(padre, width=ancho)
        selector.pack(side="left")
        return selector

    @staticmethod
    def _entrada(padre, etiqueta: str, ancho: int) -> ttk.Entry:
        ttk.Label(padre, text=etiqueta).pack(side="left", padx=(6, 3))
        entrada = ttk.Entry(padre, width=ancho)
        entrada.pack(side="left")
        return entrada

    def refrescar(self) -> None:
        self.sede.cargar([(s.nombre, s.id) for s in self.s.sedes.listar()], vacio="Todas")
        self.genero.cargar([(g, g) for g in self.s.catalogo.generos()], vacio="Todos")

    def _ajustar_filtros(self) -> None:
        filtros = self.reporte.valor().filtros
        controles = {
            "sede": (self.sede,), "genero": (self.genero,), "tipo_prestamo": (self.tipo_prestamo,),
            "tipo_remito": (self.tipo_remito,), "periodo": (self.desde, self.hasta), "limite": (self.limite,),
        }
        for clave, grupo in controles.items():
            for control in grupo:
                activo = clave in filtros
                combo = isinstance(control, Selector)
                control.configure(state=("readonly" if combo else "normal") if activo else "disabled")

    def _filtro(self) -> FiltroReporte:
        filtros = self.reporte.valor().filtros
        return FiltroReporte(
            sede_id=self.sede.valor() if "sede" in filtros else None,
            genero=self.genero.valor() if "genero" in filtros else None,
            tipo_prestamo=self.tipo_prestamo.valor() if "tipo_prestamo" in filtros else None,
            tipo_remito=self.tipo_remito.valor() if "tipo_remito" in filtros else None,
            desde=leer_fecha(self.desde.get()) if "periodo" in filtros else None,
            hasta=leer_fecha(self.hasta.get()) if "periodo" in filtros else None,
            limite=int(self.limite.get() or 10),
        )

    @accion
    def generar(self) -> None:
        self.resultado = self.reporte.valor().generar(self._filtro())
        ancho = max(90, 1150 // len(self.resultado.columnas))
        self.tabla.configurar_columnas([(c, ancho) for c in self.resultado.columnas])
        self.tabla.cargar(enumerate(self.resultado.filas))
        self.metricas.configure(text="     ".join(f"{k}: {v}" for k, v in self.resultado.metricas.items()))

    def _exportar(self, extension: str, exportador) -> None:
        if self.resultado is None:
            raise ReglaIncumplida("Primero genere el reporte")
        DIRECTORIO_SALIDAS.mkdir(exist_ok=True)
        ruta = filedialog.asksaveasfilename(
            parent=self, defaultextension=extension, initialdir=DIRECTORIO_SALIDAS,
            filetypes=[(extension.upper(), f"*{extension}")],
        )
        if ruta:
            exportador(self.resultado, Path(ruta))
            messagebox.showinfo("Reporte exportado", ruta, parent=self)

    @accion
    def pdf(self) -> None:
        self._exportar(".pdf", exportar_pdf)

    @accion
    def csv(self) -> None:
        self._exportar(".csv", exportar_csv)
