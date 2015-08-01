# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

import os

from quodlibet import config
from quodlibet.formats import AudioFile
from quodlibet.util.cover.manager import CoverManager
from quodlibet.util.path import fsnative, normalize_path

from . import TestCase, DATA_DIR


quux = AudioFile({
    "~filename": os.path.join(DATA_DIR, "asong.ogg"),
    "album": "Quuxly",
})

bar_2_1 = AudioFile({
    "~filename": fsnative("does not/exist"),
    "title": "more songs",
    "discnumber": "2/2", "tracknumber": "1",
    "artist": "Foo\nI have two artists", "album": "Bar",
    "lyricist": "Foo", "composer": "Foo", "performer": "I have two artists",
})


class TCoverManager(TestCase):

    def setUp(self):
        config.init()
        self.manager = CoverManager()

        self.dir = os.path.realpath(quux("~dirname"))
        self.files = [self.full_path("12345.jpg"),
                      self.full_path("nothing.jpg")
                      ]
        for f in self.files:
            file(f, "w").close()

    def _find_cover(self, song):
        return self.manager.get_cover(song)

    def tearDown(self):
        for f in self.files:
            os.unlink(f)
        config.quit()

    def full_path(self, path):
        return os.path.join(self.dir, path)

    def test_dir_not_exist(self):
        self.assertFalse(self._find_cover(bar_2_1))

    def test_nothing(self):
        self.assertFalse(self._find_cover(quux))

    def test_labelid(self):
        quux["labelid"] = "12345"
        self.assertEqual(os.path.abspath(self._find_cover(quux).name),
                             self.full_path("12345.jpg"))
        del(quux["labelid"])

    def test_regular(self):
        files = [os.path.join(self.dir, f) for f in
                 ["cover.png", "folder.jpg", "frontcover.jpg",
                  "front_folder_cover.gif", "jacket_cover.front.folder.jpeg"]]
        for f in files:
            file(f, "w").close()
            self.files.append(f)
            self.assertEqual(
                os.path.abspath(self._find_cover(quux).name), f)
        self.test_labelid() # labelid must work with other files present

    def test_file_encoding(self):
        if os.name == "nt":
            return

        f = self.full_path("\xff\xff\xff\xff - cover.jpg")
        file(f, "w").close()
        self.files.append(f)
        self.assertTrue(isinstance(quux("album"), str))
        h = self._find_cover(quux)
        self.assertEqual(h.name, normalize_path(f))

    def test_intelligent(self):
        song = quux
        song["artist"] = "Q-Man"
        song["title"] = "First Q falls hardest"
        files = [self.full_path(f) for f in
                 ["Quuxly - back.jpg", "Quuxly.jpg", "q-man - quxxly.jpg",
                  "folder.jpeg", "Q-man - Quuxly (FRONT).jpg"]]
        for f in files:
            file(f, "w").close()
            self.files.append(f)
            cover = self._find_cover(song)
            if cover:
                actual = os.path.abspath(cover.name)
                self.assertEqual(actual, f)
            else:
                # Here, no cover is better than the back...
                self.assertEqual(f, self.full_path("Quuxly - back.jpg"))

    def test_embedded_special_cover_words(self):
        """Tests that words incidentally containing embedded "special" words
        album keywords (e.g. cover, disc, back) don't trigger
        See Issue 818"""

        song = AudioFile({
            "~filename": fsnative("tests/data/asong.ogg"),
            "album": "foobar",
            "title": "Ode to Baz",
            "artist": "Q-Man",
        })
        files = [self.full_path(f) for f in
                 ['back.jpg',
                  'discovery.jpg', "Pharell - frontin'.jpg",
                  'nickelback - Curb.jpg',
                  'foobar.jpg', 'folder.jpg',     # Though this is debatable
                  'Q-Man - foobar.jpg', 'Q-man - foobar (cover).jpg']]
        for f in files:
            file(f, "w").close()
            self.files.append(f)
            cover = self._find_cover(song)
            if cover:
                actual = os.path.abspath(cover.name)
                self.assertEqual(
                    actual, f, "\"%s\" should trump \"%s\"" % (f, actual))
            else:
                self.assertTrue(f, self.full_path('back.jpg'))

    def test_get_thumbnail(self):
        self.assertTrue(self.manager.get_pixbuf(quux, 10, 10) is None)
        self.assertTrue(self.manager.get_pixbuf_many([quux], 10, 10) is None)
