from tkinter import ttk

from biblioteca.dominio.enums import EstadoRecepcion, TipoRemito
from biblioteca.ui.componentes import Campo, Dialogo, Pantalla, Selector, Tabla, accion, mostrar_texto

PENDIENTES = [("N°", 50), ("Libro", 240), ("Ejemplar", 90), ("Socio", 200), ("Desde", 170), ("Hacia", 170)]
REMITOS = [("N°", 50), ("Tipo", 70), ("Emisión", 150), ("Origen", 170), ("Destino", 170), ("Ejemplares", 80), ("Estado", 120)]
RECEPCIONES = [(estado.value, estado) for estado in EstadoRecepcion]


class PantallaLogistica(Pantalla):
    def construir(self) -> None:
        ttk.Label(self, text="Préstamos a la espera de envío", style="Titulo.TLabel").pack(anchor="w")
        barra = self.barra([("Generar remito", self.generar)])
        ttk.Label(barra, text="Tipo:").pack(side="left", padx=(12, 6))
        self.tipo = Selector(barra, width=12)
        self.tipo.pack(side="left")
        self.tipo.cargar([(t.value, t) for t in TipoRemito])
        self.tipo.bind("<<ComboboxSelected>>", lambda _: self.refrescar())
        self.pendientes = Tabla(self, PENDIENTES, multiple=True, vacio="No hay préstamos a la espera de este envío")
        self.pendientes.pack(fill="both", expand=True, pady=(0, 12))

        ttk.Label(self, text="Remitos", style="Titulo.TLabel").pack(anchor="w")
        self.barra([("Empaquetar", self.empaquetar), ("Despachar", self.despachar), ("Recibir", self.recibir), ("Cancelar", self.cancelar), ("Ver trazabilidad", self.trazabilidad)])
        self.remitos = Tabla(self, REMITOS, vacio="Todavía no se generaron remitos")
        self.remitos.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        tipo = self.tipo.valor()
        ida = tipo is TipoRemito.IDA
        self.pendientes.cargar(
            (p.id, (p.id, p.ejemplar.libro.titulo, p.ejemplar.codigo_inventario, str(p.socio),
                    (p.sede_origen if ida else p.sede_destino).nombre,
                    (p.sede_destino if ida else p.sede_origen).nombre))
            for p in self.s.logistica.pendientes(tipo)
        )
        self.remitos.cargar(
            (r.id, (r.id, r.tipo, r.fecha_emision.strftime("%Y-%m-%d %H:%M"), r.sede_origen.nombre,
                    r.sede_destino.nombre, len(r.detalles), r.estado.nombre))
            for r in self.s.logistica.listar()
        )

    @accion
    def generar(self) -> None:
        datos = Dialogo.pedir(self, "Generar remito", [Campo("observaciones", "Observaciones")])
        if datos:
            self.s.logistica.generar_remito(self.tipo.valor(), self.pendientes.seleccion(), datos["observaciones"])

    @accion
    def empaquetar(self) -> None:
        self.s.logistica.empaquetar(self.remitos.elegido())

    @accion
    def despachar(self) -> None:
        self.s.logistica.despachar(self.remitos.elegido())

    @accion
    def cancelar(self) -> None:
        self.s.logistica.cancelar(self.remitos.elegido())

    @accion
    def recibir(self) -> None:
        remito = self.s.logistica.obtener(self.remitos.elegido())
        campos = []
        for detalle in remito.detalles:
            nombre = f"{detalle.ejemplar.codigo_inventario} - {detalle.ejemplar.libro.titulo}"
            campos.append(Campo(f"estado_{detalle.ejemplar.id}", nombre, opciones=RECEPCIONES))
            campos.append(Campo(f"obs_{detalle.ejemplar.id}", "Observaciones"))
        datos = Dialogo.pedir(self, f"Recepción del remito {remito.id}", campos)
        if datos:
            recepciones = {
                d.ejemplar.id: (datos[f"estado_{d.ejemplar.id}"], datos[f"obs_{d.ejemplar.id}"].strip())
                for d in remito.detalles
            }
            self.s.logistica.recibir(remito.id, recepciones)

    @accion
    def trazabilidad(self) -> None:
        remito = self.s.logistica.obtener(self.remitos.elegido())
        lineas = [
            f"Remito {remito.id} ({remito.tipo}): {remito.sede_origen.nombre} -> {remito.sede_destino.nombre}",
            f"Estado actual: {remito.estado.nombre}",
            f"Emitido: {remito.fecha_emision:%Y-%m-%d %H:%M}",
            f"Observaciones: {remito.observaciones or '-'}",
            "", "Historial de estados:",
        ]
        lineas += [
            f"  {c.fecha_hora_fin:%Y-%m-%d %H:%M}  {c.estado_anterior} -> {c.estado_nuevo}"
            for c in remito.cambios
        ]
        lineas += ["", "Ejemplares:"]
        lineas += [
            f"  {d.ejemplar.codigo_inventario}  {d.ejemplar.libro.titulo}  "
            f"[recepción: {d.estado_recepcion or 'pendiente'}] {d.observaciones}"
            for d in remito.detalles
        ]
        mostrar_texto(self, f"Trazabilidad del remito {remito.id}", "\n".join(lineas))
