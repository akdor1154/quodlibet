# -*- coding: utf-8 -*-
from tests import TestCase

from gi.repository import Gtk

from quodlibet.qltk.wlw import WaitLoadWindow


class TWaitLoadWindow(TestCase):

    class DummyConnector(Gtk.Window):
        count = 0

        def connect(self, *args):
            self.count += 1

        def disconnect(self, *args):
            self.count -= 1

        class Eater:
            def set_cursor(*args):
                pass

        window = Eater()

    def setUp(self):
        self.parent = self.DummyConnector()
        self.wlw = WaitLoadWindow(self.parent, 5, "a test")

    def test_none(self):
        wlw = WaitLoadWindow(None, 5, "a test")
        wlw.step()
        wlw.destroy()

    def test_connect(self):
        self.assertEqual(2, self.parent.count)
        self.wlw.destroy()
        self.assertEqual(0, self.parent.count)

    def test_start(self):
        self.assertEqual(0, self.wlw.current)
        self.assertEqual(5, self.wlw.count)

    def test_step(self):
        self.assertFalse(self.wlw.step())
        self.assertEqual(1, self.wlw.current)
        self.assertFalse(self.wlw.step())
        self.assertFalse(self.wlw.step())
        self.assertEqual(3, self.wlw.current)

    def test_destroy(self):
        self.wlw.destroy()
        self.assertEqual(0, self.parent.count)

    def tearDown(self):
        self.wlw.destroy()
