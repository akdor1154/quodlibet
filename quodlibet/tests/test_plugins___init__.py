# -*- coding: utf-8 -*-
from tests import TestCase, mkstemp

import os

from quodlibet import config
from quodlibet.formats import AudioFile
from quodlibet.util.songwrapper import SongWrapper, ListWrapper
from quodlibet.plugins import PluginConfig


class TSongWrapper(TestCase):

    psong = AudioFile({
        "~filename": "does not/exist",
        "title": "more songs",
        "discnumber": "2/2", "tracknumber": "1",
        "artist": "Foo\nI have two artists", "album": "Bar",
        "~bookmark": "2:10 A bookmark"})
    pwrap = SongWrapper(psong)

    def setUp(self):
        fd, self.filename = mkstemp()
        os.close(fd)
        config.init()
        self.wrap = SongWrapper(AudioFile(
            {"title": "woo", "~filename": self.filename}))

    def tearDown(self):
        os.unlink(self.filename)
        config.quit()

    def test_slots(self):
        def breakme():
            self.wrap.woo = 1
        self.assertRaises(AttributeError, breakme)

    def test_cmp(self):
        songs = [SongWrapper(AudioFile({"tracknumber": str(i)}))
                 for i in range(10)]
        songs.reverse()
        songs.sort()
        self.assertEqual([s("~#track") for s in songs], list(range(10)))

    def test_needs_write_yes(self):
        self.assertFalse(self.wrap._needs_write)
        self.wrap["woo"] = "bar"
        self.assertTrue(self.wrap._needs_write)

    def test_needs_write_no(self):
        self.assertFalse(self.wrap._needs_write)
        self.wrap["~woo"] = "bar"
        self.assertFalse(self.wrap._needs_write)

    def test_pop(self):
        self.assertFalse(self.wrap._needs_write)
        self.wrap.pop("artist", None)
        self.assertTrue(self.wrap._needs_write)

    def test_getitem(self):
        self.assertEqual(self.wrap["title"], "woo")

    def test_get(self):
        self.assertEqual(self.wrap.get("title"), "woo")
        self.assertEqual(self.wrap.get("dne"), None)
        self.assertEqual(self.wrap.get("dne", "huh"), "huh")

    def test_delitem(self):
        self.assertTrue("title" in self.wrap)
        del(self.wrap["title"])
        self.assertFalse("title" in self.wrap)
        self.assertTrue(self.wrap._needs_write)

    def test_realkeys(self):
        self.assertEqual(self.pwrap.realkeys(), self.psong.realkeys())

    def test_website(self):
        self.assertEqual(self.pwrap.website(), self.psong.website())

    def test_can_change(self):
        for key in ["~foo", "title", "whee", "a test", "foo=bar", ""]:
            self.assertEqual(
                self.pwrap.can_change(key), self.psong.can_change(key))

    def test_comma(self):
        for key in ["title", "artist", "album", "notexist", "~length"]:
            self.assertEqual(self.pwrap.comma(key), self.psong.comma(key))

    def test_list(self):
        for key in ["title", "artist", "album", "notexist", "~length"]:
            self.assertEqual(self.pwrap.list(key), self.psong.list(key))

    def test_dicty(self):
        self.assertEqual(list(self.pwrap.keys()), list(self.psong.keys()))
        self.assertEqual(list(self.pwrap.values()), list(self.psong.values()))
        self.assertEqual(list(self.pwrap.items()), list(self.psong.items()))

    def test_mtime(self):
        self.wrap._song.sanitize()
        self.assertTrue(self.wrap.valid())
        self.wrap["~#mtime"] = os.path.getmtime(self.filename) - 2
        self.wrap._updated = False
        self.assertFalse(self.wrap.valid())

    def test_setitem(self):
        self.assertFalse(self.wrap._was_updated())
        self.wrap["title"] = "bar"
        self.assertTrue(self.wrap._was_updated())
        self.assertEqual(self.wrap["title"], "bar")

    def test_not_really_updated(self):
        self.assertFalse(self.wrap._was_updated())
        self.wrap["title"] = "woo"
        self.assertFalse(self.wrap._was_updated())
        self.wrap["title"] = "quux"
        self.assertTrue(self.wrap._was_updated())

    def test_new_tag(self):
        self.assertFalse(self.wrap._was_updated())
        self.wrap["version"] = "bar"
        self.assertTrue(self.wrap._was_updated())

    def test_bookmark(self):
        self.assertEqual(self.psong.bookmarks, self.pwrap.bookmarks)
        self.pwrap.bookmarks = [(43, "another mark")]
        self.assertEqual(self.psong["~bookmark"], "0:43 another mark")
        self.assertEqual(self.psong.bookmarks, self.pwrap.bookmarks)


class TListWrapper(TestCase):
    def test_empty(self):
        wrapped = ListWrapper([])
        self.assertEqual(wrapped, [])

    def test_empty_song(self):
        wrapped = ListWrapper([{}])
        self.assertTrue(len(wrapped) == 1)
        self.assertFalse(isinstance(wrapped[0], dict))

    def test_none(self):
        wrapped = ListWrapper([None, None])
        self.assertTrue(len(wrapped) == 2)
        self.assertEqual(wrapped, [None, None])


class TPluginConfig(TestCase):

    def setUp(self):
        config.init()

    def tearDown(self):
        config.quit()

    def test_mapping(self):
        c = PluginConfig("some")
        c.set("foo", "bar")
        self.assertEqual(config.get("plugins", "some_foo"), "bar")

    def test_defaults(self):
        c = PluginConfig("some")
        c.defaults.set("hm", "mh")
        self.assertEqual(c.get("hm"), "mh")
