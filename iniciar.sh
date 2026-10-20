#!/bin/sh
set -eu
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export GI_TYPELIB_PATH="$APP_DIR/lib/usr/lib64/girepository-1.0${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
export LD_LIBRARY_PATH="$APP_DIR/lib/usr/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export GDK_BACKEND=wayland
exec /usr/bin/python3 "$APP_DIR/pinta.py" "$@"
