# -*- coding: utf-8 -*-
# Copyright 2014 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import os

from tests import TestCase, DATA_DIR
from quodlibet.formats.vgm import VgmFile


class TVgmFile(TestCase):
    def setUp(self):
        self.song = VgmFile(os.path.join(DATA_DIR, 'test.vgm'))

    def test_length(self):
        self.assertAlmostEqual(2.81, self.song("~#length", 0), 1)

    def test_reload(self):
        self.song["title"] = "foobar"
        self.song.reload()
        self.assertEqual(self.song("title"), "foobar")

    def test_write(self):
        self.song.write()

    def test_can_change(self):
        self.assertEqual(self.song.can_change(), ["title"])
        self.assertTrue(self.song.can_change("title"))
        self.assertFalse(self.song.can_change("album"))

    def test_invalid(self):
        path = os.path.join(DATA_DIR, 'empty.xm')
        self.assertRaises(Exception, VgmFile, path)
