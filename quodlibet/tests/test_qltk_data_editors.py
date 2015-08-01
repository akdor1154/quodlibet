# -*- coding: utf-8 -*-
from quodlibet import config
from tests import TestCase
from quodlibet.qltk.data_editors import MultiStringEditor


class TMultiStringEditor(TestCase):

    def setUp(self):
        config.init()

    def test_no_strings(self):
        mse = MultiStringEditor("title")
        self.assertEqual(mse.get_strings(), [])
        self.assertEqual(mse.get_title(), "title")
        mse.destroy()

    def test_defaulting(self):
        defaults = ["one", "two three"]
        mse = MultiStringEditor("title", defaults)
        self.assertEqual(mse.get_strings(), defaults)
        mse.destroy()

    def tearDown(self):
        config.quit()
