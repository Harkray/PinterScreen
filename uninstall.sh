#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID == 0 ]]; then echo 'Ejecuta sin sudo.' >&2; exit 1; fi
data_dir=${XDG_DATA_HOME:-$HOME/.local/share}
read -r -p '¿Desinstalar PinterScreen? Los PNG se conservarán. [s/N] ' answer
[[ "$answer" == s || "$answer" == S ]] || exit 0
rm -f -- "$data_dir/applications/pinterscreen.desktop" "$data_dir/icons/hicolor/scalable/apps/pinterscreen.svg"
rm -rf -- "$data_dir/PinterScreen"
echo 'PinterScreen desinstalada.'
