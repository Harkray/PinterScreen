#!/usr/bin/env bash
# Instala/actualiza PinterScreen para el usuario actual, nunca como root.
set -euo pipefail
if [[ $EUID == 0 ]]; then echo 'Ejecuta como usuario normal, sin sudo.' >&2; exit 1; fi
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ ${1:-} == --github ]]; then
    command -v git >/dev/null || { echo 'Instala git: sudo dnf install git'; exit 1; }
    temp_dir=$(mktemp -d)
    trap 'rm -rf -- "$temp_dir"' EXIT
    git clone --depth 1 https://github.com/Harkray/PinterScreen.git "$temp_dir/PinterScreen"
    bash "$temp_dir/PinterScreen/install.sh"
    exit
fi
if ! /usr/bin/python3 -c "import gi, cairo; gi.require_version('Gtk', '3.0'); gi.require_version('PangoCairo', '1.0')" 2>/dev/null; then
    echo 'Se instalarán dependencias de Fedora; sudo puede pedir tu contraseña.'
    sudo dnf install -y python3-gobject python3-cairo gtk3
fi
# Preferir biblioteca del sistema. El paquete portátil incluye Fedora 44 x86_64.
if ! /usr/bin/python3 -c "import gi; gi.require_version('GtkLayerShell', '0.1')" 2>/dev/null && [[ ! -d "$source_dir/lib/usr/lib64/girepository-1.0" ]]; then
    sudo dnf install -y gtk-layer-shell
fi
data_dir=${XDG_DATA_HOME:-$HOME/.local/share}
app_dir="$data_dir/PinterScreen"
mkdir -p "$app_dir" "$data_dir/applications" "$data_dir/icons/hicolor/scalable/apps"
if [[ "$source_dir" != "$app_dir" ]]; then
    for file in pinta.py iniciar.sh install.sh uninstall.sh icon.svg README.md; do
        install -m 644 "$source_dir/$file" "$app_dir/$file"
    done
    if [[ -d "$source_dir/lib" ]]; then cp -a "$source_dir/lib" "$app_dir/"; fi
fi
chmod +x "$app_dir/iniciar.sh" "$app_dir/install.sh" "$app_dir/uninstall.sh"
install -m 644 "$source_dir/icon.svg" "$data_dir/icons/hicolor/scalable/apps/pinterscreen.svg"
# Escape paths according to the Desktop Entry Exec specification.
/usr/bin/python3 - "$app_dir" "$data_dir/applications/pinterscreen.desktop" <<'PY'
import sys
from pathlib import Path
app, target = sys.argv[1:]
command = app + '/iniciar.sh'
for char in ('\\', '"', '`', '$'):
    command = command.replace(char, '\\' + char)
command = command.replace('%', '%%')
Path(target).write_text('[Desktop Entry]\nType=Application\nName=PinterScreen\nComment=Dibuja sobre tus ventanas\nExec="' + command + '"\nIcon=pinterscreen\nTerminal=false\nCategories=Graphics;\n')
PY
command -v update-desktop-database >/dev/null && update-desktop-database "$data_dir/applications" || true
echo "PinterScreen instalada. Ábrela desde el menú de aplicaciones."
echo "Actualizar: bash \"$app_dir/install.sh\" --github"
