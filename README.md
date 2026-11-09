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
