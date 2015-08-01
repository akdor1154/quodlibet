# -*- coding: utf-8 -*-
import os

from tests import TestCase

from quodlibet.util.uri import URI
from quodlibet.util.path import is_fsnative


class TURI(TestCase):
    def setUp(s):
        s.http_uri = URI("http://www.example.com/~piman;woo?bar=quux#whee")
        s.rfile_uri = URI("file://example.com/home/piman/crazy")
        s.file_uri = URI.frompath("/home/piman/cr!azy")

    def test_unc_paths(self):
        if os.name != "nt":
            return

        self.assertEqual(
            URI.frompath("\\\\server\\share\\path"),
            r"file:////server/share/path")

    def test_leading_slashes(self):
        self.assertEqual(
            str(URI("file://" + "/foo/bar")),
            "file://" + "/foo/bar")
        self.assertEqual(
            str(URI("file://" + "//foo/bar")),
            "file://" + "//foo/bar")

        self.assertEqual(URI("file://" + "//foo/bar").path, "//foo/bar")

        self.assertEqual(
            str(URI("file://" + "///foo/bar")),
            "file://" + "///foo/bar")
        self.assertEqual(
            str(URI("file://" + "////foo/bar")),
            "file://" + "////foo/bar")

    def test_windows_path(self):
        if os.name != "nt":
            return

        win_path = "C:\\SomeDir\xe4"
        uri = URI.frompath(win_path)
        self.assertEqual(uri, "file:///C:/SomeDir%C3%A4")
        self.assertTrue(uri.is_filename)
        self.assertTrue(is_fsnative(uri.filename))
        self.assertEqual(uri.filename, win_path)

    def test_raise_windows_path(self):
        self.assertRaises(ValueError, URI, "C:\\Some\\path")

    def test_type(s):
        s.assertTrue(isinstance(s.http_uri, URI))
        s.assertTrue(isinstance(s.http_uri, str))

    # bad constructor tests
    def test_empty(s):
        s.assertRaises(ValueError, URI, "")

    def test_no_scheme(s):
        s.assertRaises(ValueError, URI, "foobar/?quux")

    def test_no_loc_or_path(s):
        s.assertRaises(ValueError, URI, "http://")

    # good constructor tests
    def test_scheme(s):
        s.assertEqual(s.http_uri.scheme, "http")

    def test_netlocl(s):
        s.assertEqual(s.http_uri.netloc, "www.example.com")

    def test_path(s):
        s.assertEqual(s.http_uri.path, "/~piman")

    def test_params(s):
        s.assertTrue(s.http_uri.params, "woo")

    def test_query(s):
        s.assertEqual(s.http_uri.query, "bar=quux")

    def test_fragment(s):
        s.assertEqual(s.http_uri.fragment, "whee")

    # unescaping
    def test_unescaped(s):
        s.assertEqual(s.file_uri.unescaped, "file:///home/piman/cr!azy")
        s.assertEqual(s.http_uri.unescaped, s.http_uri)

    # local file handling
    def test_frompath(s):
        s.assertEqual(s.file_uri, "file:///home/piman/cr%21azy")
        expected = os.path.sep + os.path.join("home", "piman", "cr!azy")
        s.assertEqual(s.file_uri.filename, expected)
        s.assertTrue(is_fsnative(s.file_uri.filename))

    def test_bad_files(s):
        s.assertRaises(ValueError, lambda: s.http_uri.filename)
        s.assertRaises(ValueError, lambda: s.http_uri.filename)

    def test_is_filename(s):
        s.assertTrue(s.file_uri.is_filename)
        s.assertFalse(s.rfile_uri.is_filename)
        s.assertFalse(s.http_uri.is_filename)
