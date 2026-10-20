#!/usr/bin/python3
"""PinterScreen — overlay de escritorio para KDE/Wayland."""
import math
import sys
from pathlib import Path
from datetime import datetime
import cairo
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo, GtkLayerShell as Layer


def render(cr, strokes):
    for tool, color, width, points in strokes:
        if not points:
            continue
        cr.set_operator(cairo.OPERATOR_CLEAR if tool == 'Borrador' else cairo.OPERATOR_OVER)
        cr.set_source_rgba(*color, 0.32 if tool == 'Resaltar' else 1)
        cr.set_line_width(width * (4 if tool == 'Resaltar' else 3 if tool == 'Borrador' else 1))
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        x, y = points[0]
        if tool == 'Texto':
            layout = PangoCairo.create_layout(cr)
            font = Pango.FontDescription('Sans')
            font.set_absolute_size(width * Pango.SCALE)
            layout.set_font_description(font)
            layout.set_text(points[1], -1)
            cr.move_to(x, y)
            PangoCairo.show_layout(cr, layout)
        elif len(points) == 1:
            cr.arc(x, y, cr.get_line_width()/2, 0, math.tau)
            cr.fill()
        elif tool in ('Línea', 'Rectángulo', 'Flecha'):
            xx, yy = points[-1]
            if tool == 'Rectángulo':
                cr.rectangle(x, y, xx-x, yy-y)
            else:
                cr.move_to(x, y)
                cr.line_to(xx, yy)
                if tool == 'Flecha' and math.hypot(xx-x, yy-y) > 1:
                    angle = math.atan2(yy-y, xx-x)
                    head = min(max(width * 3.5, 16), math.hypot(xx-x, yy-y) * 0.65)
                    for offset in (-0.5, 0.5):
                        cr.move_to(xx, yy)
                        cr.line_to(xx-head*math.cos(angle+offset), yy-head*math.sin(angle+offset))
            cr.stroke()
        else:
            cr.move_to(x, y)
            for xx, yy in points[1:]:
                cr.line_to(xx, yy)
                if tool == 'Flecha' and math.hypot(xx-x, yy-y) > 1:
                    angle = math.atan2(yy-y, xx-x)
                    head = min(max(width * 3.5, 16), math.hypot(xx-x, yy-y) * 0.65)
                    for offset in (-0.5, 0.5):
                        cr.move_to(xx, yy)
                        cr.line_to(xx-head*math.cos(angle+offset), yy-head*math.sin(angle+offset))
            cr.stroke()
    cr.set_operator(cairo.OPERATOR_OVER)


class Screen(Gtk.Window):
    def __init__(self, app, monitor, number):
        super().__init__(title='PinterScreen')
        self.app, self.number = app, number
        self.strokes, self.redo_stack, self.active = [], [], None
        self.set_app_paintable(True)
        self.set_visual(self.get_screen().get_rgba_visual())
        Layer.init_for_window(self)
        Layer.set_namespace(self, 'pinta-pantalla')
        Layer.set_monitor(self, monitor)
        Layer.set_layer(self, Layer.Layer.TOP)
        Layer.set_exclusive_zone(self, -1)
        Layer.set_keyboard_mode(self, Layer.KeyboardMode.ON_DEMAND)
        for edge in (Layer.Edge.TOP, Layer.Edge.BOTTOM, Layer.Edge.LEFT, Layer.Edge.RIGHT):
            Layer.set_anchor(self, edge, True)
        root = Gtk.Overlay()
        self.add(root)
        self.canvas = Gtk.DrawingArea()
        self.canvas.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.canvas.connect('draw', self.draw)
        self.canvas.connect('button-press-event', self.press)
        self.canvas.connect('motion-notify-event', self.motion)
        self.canvas.connect('button-release-event', self.release)
        root.add(self.canvas)
        self.bar = Gtk.Box(spacing=7)
        self.bar.set_name('toolbar')
        self.bar.set_halign(Gtk.Align.CENTER)
        self.bar.set_valign(Gtk.Align.START)
        self.controls = Gtk.Window(title='PinterScreen · herramientas')
        Layer.init_for_window(self.controls)
        Layer.set_namespace(self.controls, 'pinta-herramientas')
        Layer.set_monitor(self.controls, monitor)
        Layer.set_layer(self.controls, Layer.Layer.OVERLAY)
        Layer.set_anchor(self.controls, Layer.Edge.TOP, True)
        Layer.set_margin(self.controls, Layer.Edge.TOP, 18)
        Layer.set_exclusive_zone(self.controls, -1)
        Layer.set_keyboard_mode(self.controls, Layer.KeyboardMode.ON_DEMAND)
        self.controls.add(self.bar)
        self.controls.connect('key-press-event', self.key)
        self.controls.connect('destroy', lambda *_: Gtk.main_quit())
        self.bar.pack_start(Gtk.Label(label='✎  PinterScreen'), False, False, 5)
        self.mode = Gtk.ToggleButton(label='Dibujar')
        self.mode.connect('toggled', lambda b: app.set_drawing(b.get_active()))
        self.bar.pack_start(self.mode, False, False, 0)
        self.tool = Gtk.ComboBoxText()
        for name in ('Lápiz', 'Resaltar', 'Flecha', 'Línea', 'Rectángulo', 'Texto', 'Borrador'):
            self.tool.append_text(name)
        self.tool.set_active(0)
        self.tool.connect('changed', self.tool_changed)
        self.bar.pack_start(self.tool, False, False, 0)
        rgba = Gdk.RGBA()
        rgba.parse('#ff405c')
        self.color = Gtk.ColorButton.new_with_rgba(rgba)
        self.color.set_tooltip_text('Color del trazo')
        self.bar.pack_start(self.color, False, False, 0)
        self.size = Gtk.SpinButton.new_with_range(1, 40, 1)
        self.size.set_value(5)
        self.size.set_tooltip_text('Grosor del trazo / tamaño del texto en píxeles')
        self.bar.pack_start(self.size, False, False, 0)
        for text, tip, callback in (
            ('↶', 'Deshacer', self.undo), ('↷', 'Rehacer', self.redo),
            ('Limpiar', 'Borrar todos los trazos de esta pantalla', self.clear),
            ('PNG', 'Guardar trazos con fondo transparente', self.save),
            ('Salir', 'Cerrar todas las pantallas', lambda *_: Gtk.main_quit())):
            button = Gtk.Button(label=text)
            button.set_tooltip_text(tip)
            button.connect('clicked', callback)
            self.bar.pack_start(button, False, False, 0)
        self.connect('key-press-event', self.key)
        self.connect('destroy', lambda *_: Gtk.main_quit())
        self.show_all()
        self.controls.show_all()
        GLib.idle_add(self.input_region)

    def input_region(self):
        if self.get_window():
            if self.app.drawing:
                self.input_shape_combine_region(None)
            else:
                self.input_shape_combine_region(cairo.Region())
            self.queue_draw()
        return False

    def draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        # Compose separately so the eraser clears ink, never desktop content.
        cr.push_group()
        render(cr, self.strokes + ([self.active] if self.active else []))
        cr.pop_group_to_source()
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.paint()

    def press(self, widget, event):
        if event.button == 1 and self.app.drawing:
            c = self.color.get_rgba()
            if self.tool.get_active_text() == 'Texto':
                self.add_text(event.x, event.y)
                return True
            self.active = (self.tool.get_active_text(), (c.red, c.green, c.blue), self.size.get_value(), [(event.x, event.y)])
            widget.queue_draw()
            return True

    def tool_changed(self, combo):
        if not hasattr(self, 'size'):
            return
        if combo.get_active_text() == 'Texto':
            self.size.set_range(8, 160)
            self.size.set_value(28)
        else:
            self.size.set_range(1, 40)
            self.size.set_value(5)

    def add_text(self, x, y):
        dialog = Gtk.Dialog(title='Escribir texto', transient_for=self.controls, modal=True)
        dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Colocar texto', Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(18)
        box.add(Gtk.Label(label='Texto · usa el color y tamaño seleccionados'))
        entry = Gtk.Entry()
        entry.set_width_chars(36)
        entry.set_activates_default(True)
        entry.set_placeholder_text('Escribe aquí…')
        box.add(entry)
        dialog.show_all()
        entry.grab_focus()
        response = dialog.run()
        text = entry.get_text().strip()
        dialog.destroy()
        if response == Gtk.ResponseType.OK and text:
            c = self.color.get_rgba()
            self.strokes.append(('Texto', (c.red, c.green, c.blue), self.size.get_value(), [(x, y), text]))
            self.redo_stack.clear()
            self.canvas.queue_draw()

    def motion(self, widget, event):
        if self.active:
            self.active[3].append((event.x, event.y))
            widget.queue_draw()

    def release(self, widget, event):
        if event.button == 1 and self.active:
            self.active[3].append((event.x, event.y))
            self.strokes.append(self.active)
            self.active = None
            self.redo_stack.clear()
            widget.queue_draw()

    def undo(self, *_):
        if self.strokes:
            self.redo_stack.append(self.strokes.pop())
            self.canvas.queue_draw()

    def redo(self, *_):
        if self.redo_stack:
            self.strokes.append(self.redo_stack.pop())
            self.canvas.queue_draw()

    def clear(self, *_):
        if not self.strokes:
            return
        # An erasing operation makes clearing undoable.
        self.strokes.append(('Borrador', (0, 0, 0), max(self.canvas.get_allocated_width(), self.canvas.get_allocated_height()) * 2,
                             [(self.canvas.get_allocated_width()/2, self.canvas.get_allocated_height()/2)]))
        self.redo_stack.clear()
        self.canvas.queue_draw()

    def save(self, *_):
        target = Path(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES) or Path.home() / 'Pictures') / 'PinterScreen'
        try:
            target.mkdir(parents=True, exist_ok=True)
            path = target / f'trazos-{datetime.now():%Y%m%d-%H%M%S-%f}-pantalla-{self.number}.png'
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.canvas.get_allocated_width(), self.canvas.get_allocated_height())
            render(cairo.Context(surface), self.strokes)
            surface.write_to_png(str(path))
            self.notice(f'Guardado en:\n{path}')
        except (OSError, cairo.Error) as exc:
            self.notice(f'No se pudo guardar:\n{exc}')

    def notice(self, text):
        dialog = Gtk.MessageDialog(transient_for=self.controls, modal=True, buttons=Gtk.ButtonsType.OK, text=text)
        dialog.run()
        dialog.destroy()

    def key(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.app.set_drawing(False)
        elif event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.KEY_z:
                self.undo()
            elif event.keyval == Gdk.KEY_y:
                self.redo()


class App:
    def __init__(self):
        self.drawing = False
        self.screens = []
        display = Gdk.Display.get_default()
        if not Layer.is_supported():
            raise RuntimeError('Se necesita KDE Plasma/Wayland u otro compositor compatible con layer-shell. GNOME no es compatible.')
        css = Gtk.CssProvider()
        css.load_from_data(b'#toolbar { background: #202530; color: #fafafa; border-radius: 16px; padding: 10px; border: 1px solid #535e70; } #toolbar button, #toolbar combobox, #toolbar spinbutton { border-radius: 8px; } #toolbar button:checked { background: #7954df; color: white; }')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        for i in range(display.get_n_monitors()):
            self.screens.append(Screen(self, display.get_monitor(i), i+1))
        # Close safely on screen layout changes; reopen to adapt the overlays.
        display.connect('monitor-added', lambda *_: Gtk.main_quit())
        display.connect('monitor-removed', lambda *_: Gtk.main_quit())

    def set_drawing(self, value):
        self.drawing = value
        for screen in self.screens:
            if not value and screen.active:
                screen.strokes.append(screen.active)
                screen.active = None
                screen.redo_stack.clear()
                screen.canvas.queue_draw()
            screen.mode.set_active(value)
            screen.mode.set_label('Dibujando · Esc' if value else 'Dibujar')
            screen.input_region()


if __name__ == '__main__':
    try:
        App()
        Gtk.main()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
