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


def leer_cantidad(texto: str) -> int:
    texto = texto.strip()
    if not texto:
        return 10
    if not texto.isdigit() or int(texto) < 1:
        raise ReglaIncumplida("La cantidad debe ser un número entero mayor a cero")
    return int(texto)


class PantallaReportes(Pantalla):
    def construir(self) -> None:
        self.resultado = None
        self._grupos: dict[str, list[ttk.Frame]] = {}
        arriba = ttk.Frame(self)
        arriba.pack(fill="x", pady=(0, 10))
        self.reporte = Selector(arriba, width=46)
        self.reporte.pack(side="left", padx=(0, 8))
        self.reporte.cargar([(r.titulo, r) for r in self.s.reportes.listar()])
        self.reporte.bind("<<ComboboxSelected>>", lambda _: self._ajustar_filtros())
        ttk.Button(arriba, text="Generar reporte", style="Primario.TButton", command=self.generar).pack(side="left", padx=(0, 6))
        ttk.Button(arriba, text="Exportar PDF", command=self.pdf).pack(side="left", padx=(0, 6))
        ttk.Button(arriba, text="Exportar CSV", command=self.csv).pack(side="left")

        self.marco_filtros = ttk.Frame(self)
        self.marco_filtros.pack(fill="x", pady=(0, 12))
        self.sede = self._selector("sede", "Sede", 24)
        self.genero = self._selector("genero", "Género", 14)
        self.tipo_prestamo = self._selector("tipo_prestamo", "Préstamo", 18)
        self.tipo_prestamo.cargar([(n, n) for n in TIPOS_PRESTAMO], vacio="Todos")
        self.tipo_remito = self._selector("tipo_remito", "Remito", 10)
        self.tipo_remito.cargar([(t.value, t.value) for t in TipoRemito], vacio="Todos")
        self.desde = self._control("periodo", "Desde (AAAA-MM-DD)", lambda g: ttk.Entry(g, width=18))
        self.hasta = self._control("periodo", "Hasta (AAAA-MM-DD)", lambda g: ttk.Entry(g, width=18))
        self.limite = self._control("limite", "Cantidad", lambda g: ttk.Spinbox(g, from_=1, to=100, width=6))
        self.limite.set(10)

        self.metricas = ttk.Frame(self)
        self.metricas.pack(fill="x")
        self.tabla = Tabla(self, [("Resultado", 400)], vacio="Elegí los filtros y generá el reporte")
        self.tabla.pack(fill="both", expand=True, pady=(12, 0))
        self._ajustar_filtros()

    def _control(self, clave: str, etiqueta: str, crear):
        grupo = ttk.Frame(self.marco_filtros)
        ttk.Label(grupo, text=etiqueta, style="Campo.TLabel").pack(anchor="w")
        control = crear(grupo)
        control.pack(anchor="w")
        self._grupos.setdefault(clave, []).append(grupo)
        return control

    def _selector(self, clave: str, etiqueta: str, ancho: int) -> Selector:
        return self._control(clave, etiqueta, lambda g: Selector(g, width=ancho))

    def refrescar(self) -> None:
        self.sede.cargar([(s.nombre, s.id) for s in self.s.sedes.listar()], vacio="Todas")
        self.genero.cargar([(g, g) for g in self.s.catalogo.generos()], vacio="Todos")

    def _ajustar_filtros(self) -> None:
        filtros = self.reporte.valor().filtros
        for clave, grupos in self._grupos.items():
            for grupo in grupos:
                grupo.pack_forget()
                if clave in filtros:
                    grupo.pack(side="left", padx=(0, 14))

    def _mostrar_metricas(self, metricas: dict[str, str]) -> None:
        for hijo in self.metricas.winfo_children():
            hijo.destroy()
        for nombre, valor in metricas.items():
            bloque = ttk.Frame(self.metricas)
            bloque.pack(side="left", padx=(0, 34))
            ttk.Label(bloque, text=valor, style="Metrica.TLabel").pack(anchor="w")
            ttk.Label(bloque, text=nombre, style="Campo.TLabel").pack(anchor="w")

    def _filtro(self) -> FiltroReporte:
        filtros = self.reporte.valor().filtros
        return FiltroReporte(
            sede_id=self.sede.valor() if "sede" in filtros else None,
            genero=self.genero.valor() if "genero" in filtros else None,
            tipo_prestamo=self.tipo_prestamo.valor() if "tipo_prestamo" in filtros else None,
            tipo_remito=self.tipo_remito.valor() if "tipo_remito" in filtros else None,
            desde=leer_fecha(self.desde.get()) if "periodo" in filtros else None,
            hasta=leer_fecha(self.hasta.get()) if "periodo" in filtros else None,
            limite=leer_cantidad(self.limite.get()),
        )

    @accion
    def generar(self) -> None:
        self.resultado = self.reporte.valor().generar(self._filtro())
        ancho = max(90, 1000 // len(self.resultado.columnas))
        self.tabla.configurar_columnas([(c, ancho) for c in self.resultado.columnas])
        self.tabla.cargar(enumerate(self.resultado.filas))
        self._mostrar_metricas(self.resultado.metricas)

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
