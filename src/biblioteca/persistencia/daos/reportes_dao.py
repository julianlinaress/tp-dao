"""Consultas de los reportes de gestión."""

from biblioteca.persistencia.dao import Consultas

SOCIO = "so.apellido || ', ' || so.nombre"


class ReportesDAO(Consultas):
    def activos_y_en_transito(self, parametros: dict) -> list:
        return self._todos(
            f"""
            SELECT 'Préstamo activo' AS categoria, l.titulo, e.codigo_inventario, {SOCIO} AS socio,
                   o.nombre AS origen, d.nombre AS destino, p.fecha_retiro AS fecha,
                   'Vence ' || p.fecha_vencimiento AS referencia
            FROM prestamos p
            JOIN ejemplares e ON e.id = p.ejemplar_id JOIN libros l ON l.id = e.libro_id
            JOIN socios so ON so.id = p.socio_id
            JOIN sedes o ON o.id = p.sede_origen_id JOIN sedes d ON d.id = p.sede_destino_id
            WHERE p.estado = 'Activo'
              AND (:sede IS NULL OR :sede IN (p.sede_origen_id, p.sede_destino_id))
              AND (:tipo_prestamo IS NULL OR p.tipo = :tipo_prestamo)
              AND (:desde IS NULL OR p.fecha_retiro >= :desde)
              AND (:hasta IS NULL OR p.fecha_retiro <= :hasta)
            UNION ALL
            SELECT 'En tránsito', l.titulo, e.codigo_inventario, {SOCIO}, o.nombre, d.nombre,
                   substr(r.fecha_emision, 1, 10), 'Remito ' || r.id || ' (' || r.tipo || ')'
            FROM detalles_remito dr
            JOIN remitos r ON r.id = dr.remito_id
            JOIN prestamos p ON p.id = dr.prestamo_id
            JOIN ejemplares e ON e.id = dr.ejemplar_id JOIN libros l ON l.id = e.libro_id
            JOIN socios so ON so.id = p.socio_id
            JOIN sedes o ON o.id = r.sede_origen_id JOIN sedes d ON d.id = r.sede_destino_id
            WHERE r.estado = 'EnTransito'
              AND (:sede IS NULL OR :sede IN (r.sede_origen_id, r.sede_destino_id))
              AND (:tipo_prestamo IS NULL OR p.tipo = :tipo_prestamo)
              AND (:desde IS NULL OR substr(r.fecha_emision, 1, 10) >= :desde)
              AND (:hasta IS NULL OR substr(r.fecha_emision, 1, 10) <= :hasta)
            ORDER BY categoria, fecha
            """,
            parametros,
        )

    def vencidos_y_multas(self, parametros: dict) -> list:
        vencido = "(p.estado = 'Activo' AND p.fecha_vencimiento < :hoy)"
        return self._todos(
            f"""
            SELECT so.dni, {SOCIO} AS socio,
                   SUM({vencido}) AS vencidos,
                   CAST(MAX(CASE WHEN {vencido}
                            THEN julianday(:hoy) - julianday(p.fecha_vencimiento)
                            ELSE COALESCE(m.dias_atraso, 0) END) AS INTEGER) AS mayor_atraso,
                   COUNT(m.id) AS multas,
                   COALESCE(SUM(m.monto), 0) AS total,
                   COALESCE(SUM(CASE WHEN m.es_pagada = 0 THEN m.monto END), 0) AS impago
            FROM prestamos p
            JOIN socios so ON so.id = p.socio_id
            LEFT JOIN multas m ON m.prestamo_id = p.id
            WHERE ({vencido} OR m.id IS NOT NULL)
              AND (:sede IS NULL OR p.sede_destino_id = :sede)
              AND (:desde IS NULL OR p.fecha_vencimiento >= :desde)
              AND (:hasta IS NULL OR p.fecha_vencimiento <= :hasta)
            GROUP BY so.id
            ORDER BY impago DESC, vencidos DESC, socio
            """,
            parametros,
        )

    def libros_mas_solicitados(self, parametros: dict) -> list:
        return self._todos(
            """
            SELECT l.titulo, l.autor, l.genero, COUNT(*) AS solicitudes,
                   COUNT(DISTINCT p.sede_destino_id) AS sedes_destino,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS participacion
            FROM prestamos p
            JOIN ejemplares e ON e.id = p.ejemplar_id JOIN libros l ON l.id = e.libro_id
            WHERE p.tipo = 'Interbibliotecario'
              AND (:sede IS NULL OR p.sede_destino_id = :sede)
              AND (:genero IS NULL OR l.genero = :genero)
              AND (:desde IS NULL OR p.fecha_solicitud >= :desde)
              AND (:hasta IS NULL OR p.fecha_solicitud <= :hasta)
            GROUP BY l.id
            ORDER BY solicitudes DESC, l.titulo
            LIMIT :limite
            """,
            parametros,
        )

    def disponibilidad_por_sede(self, parametros: dict) -> list:
        return self._todos(
            """
            SELECT s.nombre AS sede, l.titulo, COUNT(*) AS total,
                   SUM(e.estado_circulacion = 'Disponible') AS disponibles,
                   SUM(e.estado_circulacion = 'Reservado') AS reservados,
                   SUM(e.estado_circulacion = 'Prestado') AS prestados,
                   SUM(e.estado_circulacion IN ('EnTransito', 'PendienteRetorno')) AS en_movimiento,
                   SUM(e.estado_circulacion = 'FueraDeServicio') AS fuera_de_servicio
            FROM ejemplares e
            JOIN sedes s ON s.id = e.sede_id JOIN libros l ON l.id = e.libro_id
            WHERE (:sede IS NULL OR e.sede_id = :sede)
              AND (:genero IS NULL OR l.genero = :genero)
            GROUP BY s.id, l.id
            ORDER BY s.nombre, l.titulo
            """,
            parametros,
        )

    def resultado_de_envios(self, parametros: dict) -> list:
        return self._todos(
            """
            SELECT o.nombre AS origen, COUNT(DISTINCT r.id) AS remitos, COUNT(*) AS ejemplares,
                   SUM(dr.estado_recepcion = 'OK') AS ok,
                   SUM(dr.estado_recepcion = 'Dañado') AS danados,
                   SUM(dr.estado_recepcion = 'Destruido') AS destruidos,
                   SUM(dr.estado_recepcion = 'Extraviado') AS extraviados,
                   ROUND(SUM(dr.estado_recepcion = 'OK') * 100.0 / COUNT(*), 1) AS tasa_exito
            FROM detalles_remito dr
            JOIN remitos r ON r.id = dr.remito_id
            JOIN sedes o ON o.id = r.sede_origen_id
            WHERE r.estado IN ('Recibido', 'ConIncidencia')
              AND (:sede IS NULL OR r.sede_origen_id = :sede)
              AND (:tipo_remito IS NULL OR r.tipo = :tipo_remito)
              AND (:desde IS NULL OR substr(r.fecha_emision, 1, 10) >= :desde)
              AND (:hasta IS NULL OR substr(r.fecha_emision, 1, 10) <= :hasta)
            GROUP BY r.sede_origen_id
            ORDER BY tasa_exito, origen
            """,
            parametros,
        )

    def movimiento_entre_sedes(self, parametros: dict) -> list:
        return self._todos(
            """
            SELECT o.nombre AS origen, d.nombre AS destino, r.tipo,
                   COUNT(*) AS envios,
                   SUM((SELECT COUNT(*) FROM detalles_remito dr WHERE dr.remito_id = r.id)) AS ejemplares,
                   ROUND(AVG((julianday(c.fecha_hora_fin) - julianday(c.fecha_hora_inicio)) * 24), 1)
                       AS horas_promedio
            FROM remitos r
            JOIN cambios_estado c ON c.remito_id = r.id AND c.estado_anterior = 'EnTransito'
            JOIN sedes o ON o.id = r.sede_origen_id JOIN sedes d ON d.id = r.sede_destino_id
            WHERE (:sede IS NULL OR :sede IN (r.sede_origen_id, r.sede_destino_id))
              AND (:tipo_remito IS NULL OR r.tipo = :tipo_remito)
              AND (:desde IS NULL OR substr(c.fecha_hora_inicio, 1, 10) >= :desde)
              AND (:hasta IS NULL OR substr(c.fecha_hora_inicio, 1, 10) <= :hasta)
            GROUP BY r.sede_origen_id, r.sede_destino_id, r.tipo
            ORDER BY envios DESC, origen, destino
            """,
            parametros,
        )
