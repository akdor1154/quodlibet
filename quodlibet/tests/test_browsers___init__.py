# -*- coding: utf-8 -*-
import sys
from tests import TestCase

from quodlibet import browsers
browsers.init()


class TBrowsers(TestCase):
    def test_presence(self):
        self.assertTrue(browsers.empty)
        self.assertTrue(browsers.search)
        self.assertTrue(browsers.paned)
        self.assertTrue(browsers.iradio)
        self.assertTrue(browsers.audiofeeds)
        self.assertTrue(browsers.albums)
        self.assertTrue(browsers.playlists)
        self.assertTrue(browsers.filesystem)

    def test_get(self):
        self.assertTrue(browsers.get("EmptyBar") is browsers.empty.EmptyBar)
        self.assertTrue(
            browsers.get("FileSystem") is browsers.filesystem.FileSystem)
        self.assertEqual(browsers.get("Paned"), browsers.paned.PanedBrowser)
        self.assertEqual(browsers.get("paned"), browsers.paned.PanedBrowser)
        self.assertEqual(browsers.get("panedbrowser"),
                         browsers.paned.PanedBrowser)

    def test_default(self):
        self.assertEqual(browsers.default, browsers.search.SearchBar)

    def test_name(self):
        self.assertEqual(browsers.name(browsers.empty.EmptyBar), "Disabled")

    def test_get_invalid(self):
        self.assertRaises(ValueError, browsers.get, "DoesNotExist")

    def test_index(self):
        self.assertEqual(
            browsers.browsers[browsers.index("EmptyBar")],
            browsers.empty.EmptyBar)
        self.assertEqual(
            browsers.browsers[browsers.index("FileSystem")],
            browsers.filesystem.FileSystem)

    def test_index_invalid(self):
        self.assertRaises(ValueError, browsers.index, "DoesNotExist")

    def test_migrate(self):
        self.assertTrue(
            sys.modules["browsers.audiofeeds"] is browsers.audiofeeds)
        self.assertTrue(
            sys.modules["browsers.iradio"] is browsers.iradio)

    def test_old_names(self):
        self.assertEqual(browsers.get("PanedBrowser"),
                         browsers.get("Paned"))
        self.assertEqual(browsers.get("PlaylistsBrowser"),
                         browsers.get("Playlists"))
