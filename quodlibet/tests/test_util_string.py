# -*- coding: utf-8 -*-
from tests import TestCase

from quodlibet.util.string.splitters import split_value
from quodlibet.util.string import isascii


class Tsplit_value(TestCase):
    def test_single(self):
        self.assertEqual(split_value("a b"), ["a b"])

    def test_double(self):
        self.assertEqual(split_value("a, b"), ["a", "b"])

    def test_custom_splitter(self):
        self.assertEqual(split_value("a b", [" "]), ["a", "b"])

    def test_two_splitters(self):
        self.assertEqual(
            split_value("a, b and c", [",", "and"]), ["a", "b and c"])

    def test_no_splitters(self):
        self.assertEqual(split_value("a b", []), ["a b"])

    def test_wordboundry(self):
        self.assertEqual(
            split_value("Andromeda and the Band", ["and"]),
            ["Andromeda", "the Band"])

    def test_unicode_wordboundry(self):
        val = '\xe3\x81\x82&\xe3\x81\x84'.decode('utf-8')
        self.assertEqual(split_value(val), val.split("&"))


class Tisascii(TestCase):

    def test_main(self):
        self.assertTrue(isascii(""))
        self.assertTrue(isascii(""))
        self.assertTrue(isascii("abc"))
        self.assertTrue(isascii("abc"))
        self.assertFalse(isascii("\xffbc"))
        self.assertFalse(isascii("übc"))
