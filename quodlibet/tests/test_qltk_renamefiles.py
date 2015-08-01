# -*- coding: utf-8 -*-
import os

from tests import TestCase

from quodlibet.qltk.renamefiles import (SpacesToUnderscores,
    StripWindowsIncompat)
from quodlibet.qltk.renamefiles import StripDiacriticals, StripNonASCII
from quodlibet.qltk.renamefiles import Lowercase
from quodlibet.util.path import fsnative, is_fsnative


class TFilter(TestCase):
    def setUp(self):
        self.c = self.Kind()

    def tearDown(self):
        self.c.destroy()


class TFilterMixin(object):

    def test_empty(self):
        empty = fsnative("")
        v = self.c.filter(empty, empty)
        self.assertEqual(v, empty)
        self.assertTrue(is_fsnative(v))

    def test_safe(self):
        empty = fsnative("")
        safe = fsnative("safe")
        self.assertEqual(self.c.filter(empty, safe), safe)


class TSpacesToUnderscores(TFilter):
    Kind = SpacesToUnderscores

    def test_conv(self):
        self.assertEqual(self.c.filter("", "foo bar "), "foo_bar_")


class TStripWindowsIncompat(TFilter):
    Kind = StripWindowsIncompat

    def test_conv(self):
        if os.name == "nt":
            self.assertEqual(
                self.c.filter("", 'foo\\:*?;"<>|/'), "foo\\_________")
        else:
            self.assertEqual(
                self.c.filter("", 'foo\\:*?;"<>|/'), "foo_________/")

    def test_type(self):
        empty = fsnative("")
        self.assertTrue(is_fsnative(self.c.filter(empty, empty)))

    def test_ends_with_dots_or_spaces(self):
        empty = fsnative("")
        v = self.c.filter(empty, fsnative('foo. . '))
        self.assertEqual(v, fsnative("foo. ._"))
        self.assertTrue(is_fsnative(v))

        if os.name == "nt":
            self.assertEqual(
                self.c.filter(empty, 'foo. \\bar .'), "foo._\\bar _")
        else:
            self.assertEqual(
                self.c.filter(empty, 'foo. /bar .'), "foo._/bar _")


class TStripDiacriticals(TFilter):
    Kind = StripDiacriticals

    def test_conv(self):
        empty = fsnative("")
        test = fsnative("\u00c1 test")
        out = fsnative("A test")
        v = self.c.filter(empty, test)
        self.assertEqual(v, out)
        self.assertTrue(is_fsnative(v))


class TStripNonASCII(TFilter):
    Kind = StripNonASCII

    def test_conv(self):
        empty = fsnative("")
        in_ = fsnative("foo \u00c1 \u1234")
        out = fsnative("foo _ _")
        v = self.c.filter(empty, in_)
        self.assertEqual(v, out)
        self.assertTrue(is_fsnative(v))


class TLowercase(TFilter):
    Kind = Lowercase

    def test_conv(self):
        empty = fsnative("")

        v = self.c.filter(empty, fsnative("foobar baz"))
        self.assertEqual(v, fsnative("foobar baz"))
        self.assertTrue(is_fsnative(v))

        v = self.c.filter(empty, fsnative("Foobar.BAZ"))
        self.assertEqual(v, fsnative("foobar.baz"))
        self.assertTrue(is_fsnative(v))
