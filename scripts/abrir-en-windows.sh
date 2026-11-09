#!/usr/bin/env bash
# Desde WSL: copia el código a una carpeta de Windows y abre la app nativa.
# La base y los reportes exportados quedan en esa carpeta entre ejecuciones.
set -euo pipefail

raiz="$(cd "$(dirname "$0")/.." && pwd)"
cd /mnt/c
perfil="$(cmd.exe /c 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r')"
destino="$(wslpath -u "$perfil")/tp-dao"

mkdir -p "$destino"
rm -rf "$destino/src"
cp -r "$raiz/src" "$raiz/pyproject.toml" "$raiz/README.md" "$destino/"
find "$destino/src" -type d -name __pycache__ -prune -exec rm -rf {} +

cd "$destino"
python="$destino/.venv/Scripts/python.exe"
if [[ ! -x "$python" || pyproject.toml -nt .venv/instalado ]]; then
    python.exe -m venv .venv
    "$python" -m pip install --quiet --disable-pip-version-check -e .
    touch .venv/instalado
fi

if [[ "${1:-}" != "--solo-preparar" ]]; then
    "$python" -m biblioteca
fi
