"""Punto de entrada de la aplicación."""

import tkinter as tk


def main() -> None:
    ventana = tk.Tk()
    ventana.title("Sistema de Préstamos Interbibliotecarios")
    ventana.geometry("1024x700")
    ventana.mainloop()


if __name__ == "__main__":
    main()
