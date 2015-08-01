# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

from tests.plugin import PluginTestCase

from quodlibet import config
from quodlibet.util.path import fsnative
from quodlibet.formats import AudioFile


SONGS = [
    AudioFile({
        "title": "one",
        "artist": "piman",
        "~filename": fsnative("/dev/null"),
    }),
    AudioFile({
        "title": "\xf6\xe4\xfc",
        "~filename": fsnative("/dev/zero"),
    }),
    AudioFile({
        "title": "three",
        "artist": "boris",
        "~filename": fsnative("/bin/ls"),
    }),
]

for song in SONGS:
    song.sanitize()


class THTMLExport(PluginTestCase):
    def setUp(self):
        config.init()
        self.mod = self.modules["Export to HTML"]
        self.to_html = self.mod.to_html

    def test_empty_export(self):
        text = self.to_html([])
        self.assertTrue("<html" in text)

    def test_export(self):
        text = self.to_html(SONGS)
        self.assertTrue("\xf6\xe4\xfc".encode("utf-8") in text)

    def tearDown(self):
        config.quit()
