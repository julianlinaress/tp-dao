"""Punto de entrada de la aplicación."""

from biblioteca.config import RUTA_BASE_DATOS
from biblioteca.contenedor import Servicios
from biblioteca.ui.aplicacion import Aplicacion


def main() -> None:
    servicios = Servicios(RUTA_BASE_DATOS)
    servicios.reservas.vencer_vencidas()
    Aplicacion(servicios, RUTA_BASE_DATOS).mainloop()


if __name__ == "__main__":
    main()
