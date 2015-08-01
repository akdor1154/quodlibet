# -*- coding: utf-8 -*-
from tests import TestCase, init_fake_app, destroy_fake_app

from quodlibet.formats import AudioFile
from quodlibet.library import SongLibrary
from quodlibet.util.path import fsnative
from quodlibet.qltk.information import Information
import quodlibet.config


def AF(*args, **kwargs):
    a = AudioFile(*args, **kwargs)
    a.sanitize()
    return a


class TInformation(TestCase):

    def setUp(self):
        quodlibet.config.init()
        init_fake_app()
        self.library = SongLibrary()

    def tearDown(self):
        destroy_fake_app()
        self.library.destroy()
        quodlibet.config.quit()

    def test_none(self):
        Information(self.library, []).destroy()

    def test_one(self):
        f = AF({"~filename": fsnative("/dev/null")})
        Information(self.library, [f]).destroy()

    def test_two(self):
        f = AF({"~filename": fsnative("/dev/null")})
        f2 = AF({"~filename": fsnative("/dev/null2")})
        Information(self.library, [f, f2]).destroy()

    def test_album(self):
        f = AF({"~filename": fsnative("/dev/null"), "album": "woo"})
        f2 = AF({"~filename": fsnative("/dev/null2"), "album": "woo"})
        Information(self.library, [f, f2]).destroy()

    def test_artist(self):
        f = AF({"~filename": fsnative("/dev/null"), "artist": "woo"})
        f2 = AF({"~filename": fsnative("/dev/null2"), "artist": "woo"})
        Information(self.library, [f, f2]).destroy()
