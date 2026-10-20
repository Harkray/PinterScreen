# ✏️ PinterScreen

Dibuja sobre tus ventanas en **Fedora KDE Plasma con Wayland**.
Lápiz, resaltador, flechas, líneas, rectángulos, texto, borrador,
deshacer/rehacer y PNG con fondo transparente. Una barra por monitor.

## Instalar desde GitHub

```bash
git clone https://github.com/Harkray/PinterScreen.git
cd PinterScreen
bash install.sh
```

Busca **PinterScreen** en el menú de aplicaciones. Si falta git:
`sudo dnf install git`. El instalador solo usa sudo si faltan dependencias
oficiales de Fedora. El código de la app se instala para tu usuario.

Para instalar desde el ZIP, descomprímelo y ejecuta `bash install.sh`.
Para probar sin instalar, ejecuta `bash iniciar.sh`.

## Uso

1. Pulsa **Dibujar** en la barra superior.
2. Selecciona la herramienta, el color y el grosor.
3. Arrastra con el botón izquierdo para dibujar. En **Flecha**, arrastra
   desde el inicio hacia la punta.
4. En **Texto**, el grosor pasa a ser el tamaño de letra. Pulsa sobre
   la pantalla, escribe y confirma con **Colocar texto** o Intro.
5. Desactiva **Dibujando · Esc** para usar las ventanas conservando los trazos.
   Escape también funciona cuando la app tiene el foco.
6. **↶ / ↷** deshacen y rehacen, incluidos texto, borrador y Limpiar.
7. **PNG** guarda solo los trazos en `Imágenes/PinterScreen`.
8. **Salir** cierra la app. Los trazos no se guardan automáticamente.

La barra es independiente y permanece accesible en ambos modos.
Ctrl+Z y Ctrl+Y funcionan con la capa enfocada. Cada monitor tiene sus
propios trazos; el modo de dibujo es común. Al cambiar los monitores,
la app se cierra y debe abrirse otra vez.

## Actualizar

```bash
bash "${XDG_DATA_HOME:-$HOME/.local/share}/PinterScreen/install.sh" --github
```

Cierra y vuelve a abrir la app para usar la nueva versión. Guarda los PNG
antes de cerrar. La actualización es manual.

## Desinstalar

```bash
bash "${XDG_DATA_HOME:-$HOME/.local/share}/PinterScreen/uninstall.sh"
```

Los PNG exportados se conservan.

## Compatibilidad

Probada programáticamente en Fedora 44 x86_64 con KDE y Wayland.
Requiere Python 3, PyGObject, Cairo, GTK 3, Pango y gtk-layer-shell.
**GNOME Wayland y X11 no están soportados.**
El repositorio usa gtk-layer-shell del sistema. El ZIP portátil incluye
la biblioteca oficial de Fedora 44 x86_64 y sus licencias.
No necesita red para dibujar; solo para instalar dependencias y actualizar.

## Desarrollo

```bash
python3 -m unittest discover -s tests
```

Las pruebas cubren renderizado de flechas y texto Unicode, transparencia y
borrador. Las comprobaciones GTK verifican capas y cambios de modo en una
sesión KDE/Wayland. La interacción física sobre otras ventanas requiere
comprobación manual.
