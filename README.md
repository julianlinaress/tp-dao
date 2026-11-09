# Sistema de Préstamos Interbibliotecarios

TP Integrador 2026 de Desarrollo de Aplicaciones con Objetos (UTN FRC), Tema 1.

## Stack

- Python 3.14 orientado a objetos
- Tkinter para la interfaz gráfica
- SQLite (`sqlite3`) con patrón DAO
- ReportLab y Matplotlib para los reportes
- Patrones State (remito y ejemplar) y Strategy (multas)

## Uso

```bash
uv sync
uv run biblioteca
uv run pytest
```

Desde WSL, `./scripts/abrir-en-windows.sh` abre la aplicación nativa de Windows. Copia el código a
`%USERPROFILE%\tp-dao`, donde también quedan la base y los reportes. Requiere Python 3.14 en Windows.

Para una demostración, usar **Archivo > Cargar datos de ejemplo** con la base vacía. Los tests de
interfaz necesitan un display; sin entorno gráfico: `xvfb-run -a uv run pytest`.

## Reportes

Préstamos activos y en tránsito, vencidos y multas, libros más solicitados, disponibilidad por sede,
tasa de envíos e incidencias, y movimiento entre sedes. Se filtran y exportan a PDF o CSV.

## Estructura

```text
src/biblioteca/
  config.py       reglas de negocio parametrizadas
  dominio/        entidades y patrones
  persistencia/   conexión SQLite y DAOs
  servicios/      casos de uso y validaciones
  reportes/       consultas y generación de PDF
  ui/             pantallas Tkinter
tests/
```
