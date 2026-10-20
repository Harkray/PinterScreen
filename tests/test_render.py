import importlib.util
from pathlib import Path
import unittest
import cairo

spec = importlib.util.spec_from_file_location('pinta', Path(__file__).resolve().parents[1] / 'pinta.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RenderTests(unittest.TestCase):
    def surface(self, strokes):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 160)
        m.render(cairo.Context(surface), strokes)
        surface.flush()
        return surface

    def alpha(self, s, x, y):
        return bytes(s.get_data())[y*s.get_stride()+x*4+3]

    def test_arrow_has_shaft_and_head(self):
        s = self.surface([('Flecha', (1, 0, 0), 4, [(20, 80), (160, 80)])])
        self.assertGreater(self.alpha(s, 80, 80), 0)
        self.assertGreater(self.alpha(s, 147, 73), 0)
        self.assertEqual(self.alpha(s, 20, 20), 0)

    def test_unicode_text_renders_and_can_be_erased(self):
        text = ('Texto', (1, 1, 1), 30, [(10, 10), '¡Hola, lápiz! ñ'])
        s = self.surface([text])
        self.assertTrue(any(bytes(s.get_data())))
        cleared = self.surface([text, ('Borrador', (0, 0, 0), 200, [(100, 80)])])
        self.assertFalse(any(bytes(cleared.get_data())))

    def test_dot_and_eraser_preserve_other_ink(self):
        strokes = [('Lápiz', (1, 0, 0), 10, [(10, 80), (180, 80)]),
                   ('Borrador', (0, 0, 0), 10, [(80, 80)])]
        s = self.surface(strokes)
        self.assertEqual(self.alpha(s, 80, 80), 0)
        self.assertEqual(self.alpha(s, 20, 80), 255)

if __name__ == '__main__':
    unittest.main()
