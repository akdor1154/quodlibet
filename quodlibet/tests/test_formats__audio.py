# -*- coding: utf-8 -*-
from tests import TestCase, DATA_DIR

import os

from quodlibet import config
from quodlibet.util.path import is_fsnative, fsnative, fsdecode
from quodlibet.formats import AudioFile
from quodlibet.formats._audio import INTERN_NUM_DEFAULT
from quodlibet.formats import decode_value


bar_1_1 = AudioFile({
    "~filename": fsnative("/fakepath/1"),
    "title": "A song",
    "discnumber": "1/2", "tracknumber": "1/3",
    "artist": "Foo", "album": "Bar"})
bar_1_2 = AudioFile({
    "~filename": fsnative("/fakepath/2"),
    "title": "Perhaps another",
    "discnumber": "1", "tracknumber": "2/3",
    "artist": "Lali-ho!", "album": "Bar",
    "date": "2004-12-12", "originaldate": "2005-01-01",
    "~#filesize": 1024 ** 2})
bar_2_1 = AudioFile({
    "~filename": fsnative("does not/exist"),
    "title": "more songs",
    "discnumber": "2/2", "tracknumber": "1",
    "artist": "Foo\nI have two artists", "album": "Bar",
    "lyricist": "Foo", "composer": "Foo", "performer": "I have two artists"})
bar_va = AudioFile({
    "~filename": "/fakepath/3",
    "title": "latest",
    "artist": "Foo\nI have two artists",
    "album": "Bar",
    "albumartist": "Various Artists",
    "performer": "Jay-Z"})

quux = AudioFile({
    "~filename": os.path.join(DATA_DIR, "asong.ogg"),
    "album": "Quuxly"
    })

num_call = AudioFile({"custom": "0.3"})


class TAudioFile(TestCase):
    def setUp(self):
        config.RATINGS = config.HardCodedRatingsPrefs()
        open(quux["~filename"], "w")

    def test_sort(self):
        l = [quux, bar_1_2, bar_2_1, bar_1_1]
        l.sort()
        self.assertEqual(l, [bar_1_1, bar_1_2, bar_2_1, quux])
        self.assertEqual(quux, quux)
        self.assertEqual(bar_1_1, bar_1_1)
        self.assertNotEqual(bar_2_1, bar_1_2)

    def test_realkeys(self):
        self.assertFalse("artist" in quux.realkeys())
        self.assertFalse("~filename" in quux.realkeys())
        self.assertTrue("album" in quux.realkeys())

    def test_iterrealitems(self):
        self.assertEqual(
            list(quux.iterrealitems()),
            [('album', 'Quuxly')])

    def test_trackdisc(self):
        self.assertEqual(bar_1_1("~#track"), 1)
        self.assertEqual(bar_1_1("~#disc"), 1)
        self.assertEqual(bar_1_1("~#tracks"), 3)
        self.assertEqual(bar_1_1("~#discs"), 2)
        self.assertFalse(bar_1_2("~#discs"))
        self.assertFalse(bar_2_1("~#tracks"))

    def test_call(self):
        # real keys should lookup the same
        for key in bar_1_1.realkeys():
            self.assertEqual(bar_1_1[key], bar_1_1(key))

        # fake/generated key checks
        self.assertFalse(quux("not a key"))
        self.assertEqual(quux("not a key", "foo"), "foo")
        self.assertEqual(quux("artist"), "")
        self.assertEqual(quux("~basename"), "asong.ogg")
        self.assertEqual(quux("~dirname"), DATA_DIR)
        self.assertEqual(quux("title"), "asong.ogg [Unknown]")

        self.assertEqual(bar_1_1("~#disc"), 1)
        self.assertEqual(bar_1_2("~#disc"), 1)
        self.assertEqual(bar_2_1("~#disc"), 2)
        self.assertEqual(bar_1_1("~#track"), 1)
        self.assertEqual(bar_1_2("~#track"), 2)
        self.assertEqual(bar_2_1("~#track"), 1)

    def test_year(self):
        self.assertEqual(bar_1_2("~year"), "2004")
        self.assertEqual(bar_1_2("~#year"), 2004)
        self.assertEqual(bar_1_1("~#year", 1999), 1999)

    def test_filesize(self):
        self.assertEqual(bar_1_2("~filesize"), "1.00 MB")
        self.assertEqual(bar_1_2("~#filesize"), 1024 ** 2)

    def test_originalyear(self):
        self.assertEqual(bar_1_2("~originalyear"), "2005")
        self.assertEqual(bar_1_2("~#originalyear"), 2005)
        self.assertEqual(bar_1_1("~#originalyear", 1999), 1999)

    def test_call_people(self):
        self.assertEqual(quux("~people"), "")
        self.assertEqual(bar_1_1("~people"), "Foo")
        self.assertEqual(bar_1_2("~people"), "Lali-ho!")
        self.assertEqual(bar_2_1("~people"), "Foo\nI have two artists")
        # See Issue 1034
        self.assertEqual(bar_va("~people"),
                             "Foo\nI have two artists\nVarious Artists\nJay-Z")

    def test_call_multiple(self):
        for song in [quux, bar_1_1, bar_2_1]:
            self.assertEqual(song("~~people"), song("~people"))
            self.assertEqual(song("~title~people"), song("title"))
            self.assertEqual(
                song("~title~~people"), song("~title~artist"))
            self.assertEqual(
                song("~title~~#tracks"), song("~title~~#tracks"))

    def test_tied_filename_numeric(self):
        self.assertEqual(
            bar_1_2("~~filename~~#originalyear"), '/fakepath/2 - 2005')

    def test_call_numeric(self):
        self.assertAlmostEqual(num_call("~#custom"), 0.3)
        self.assertEqual(num_call("~#blah~foo", 0), 0)

    def test_list(self):
        for key in bar_1_1.realkeys():
            self.assertEqual(bar_1_1.list(key), [bar_1_1(key)])

        self.assertEqual(quux.list("artist"), [])
        self.assertEqual(quux.list("title"), [quux("title")])
        self.assertEqual(quux.list("not a key"), [])

        self.assertEqual(len(bar_2_1.list("artist")), 2)
        self.assertEqual(bar_2_1.list("artist"),
                             bar_2_1["artist"].split("\n"))

    def test_list_separate(self):
        for key in bar_1_1.realkeys():
            self.assertEqual(bar_1_1.list_separate(key), [bar_1_1(key)])

        self.assertEqual(bar_2_1.list_separate("~artist~album"),
                             ['Foo - Bar', 'I have two artists - Bar'])

        self.assertEqual(bar_2_1.list_separate("~artist~~#track"),
                             ['Foo - 1', 'I have two artists - 1'])

    def test_list_list_separate_types(self):
        res = bar_2_1.list_separate("~~#track~artist~~filename")
        self.assertEqual(res, ['1 - Foo - does not/exist',
                               '1 - I have two artists - does not/exist'])

    def test_comma(self):
        for key in bar_1_1.realkeys():
            self.assertEqual(bar_1_1.comma(key), bar_1_1(key))
        self.assertTrue(", " in bar_2_1.comma("artist"))

    def test_comma_filename(self):
        self.assertTrue(isinstance(bar_1_1.comma("~filename"), str))

    def test_exist(self):
        self.assertFalse(bar_2_1.exists())
        self.assertTrue(quux.exists())

    def test_valid(self):
        self.assertFalse(bar_2_1.valid())

        quux["~#mtime"] = 0
        self.assertFalse(quux.valid())
        quux["~#mtime"] = os.path.getmtime(quux["~filename"])
        self.assertTrue(quux.valid())
        os.utime(quux["~filename"], (quux["~#mtime"], quux["~#mtime"] - 1))
        self.assertFalse(quux.valid())
        quux["~#mtime"] = os.path.getmtime(quux["~filename"])
        self.assertTrue(quux.valid())

        os.utime(quux["~filename"], (quux["~#mtime"], quux["~#mtime"] - 1))
        quux.sanitize()
        self.assertTrue(quux.valid())

    def test_can_change(self):
        self.assertFalse(quux.can_change("~foobar"))
        self.assertFalse(quux.can_change("=foobar"))
        self.assertFalse(quux.can_change("foo=bar"))
        self.assertFalse(quux.can_change(""))
        self.assertTrue(quux.can_change("foo bar"))

    def test_is_writable(self):
        self.assertTrue(quux.is_writable())
        os.chmod(quux["~filename"], 0o444)
        self.assertFalse(quux.is_writable())
        os.chmod(quux["~filename"], 0o644)
        self.assertTrue(quux.is_writable())

    def test_can_multiple_values(self):
        self.assertEqual(quux.can_multiple_values(), True)
        self.assertTrue(quux.can_multiple_values("artist"))

    def test_rename(self):
        old_fn = quux("~basename")
        new_fn = fsnative("anothersong.mp3")
        dir = DATA_DIR
        self.assertTrue(quux.exists())
        quux.rename(new_fn)
        self.assertFalse(os.path.exists(dir + old_fn),
                    "%s already exists" % (dir + old_fn))
        self.assertTrue(quux.exists())
        quux.rename(old_fn)
        self.assertFalse(os.path.exists(dir + new_fn))
        self.assertTrue(quux.exists())

        # move out of parent dir and back
        quux.rename(fsnative("/tmp/more_test_data"))
        self.assertFalse(os.path.exists(dir + old_fn))
        self.assertTrue(quux.exists())
        quux.rename(dir + old_fn)
        self.assertTrue(quux.exists())

    def test_rename_to_existing(self):
        quux.rename(quux("~basename"))
        if os.name != "nt":
            self.assertRaises(
                ValueError, quux.rename, fsnative("/dev/null"))
        self.assertRaises(ValueError, quux.rename,
                              os.path.join(DATA_DIR, "silence-44-s.ogg"))

    def test_website(self):
        song = AudioFile()
        song["comment"] = "www.foo"
        song["contact"] = "eh@foo.org"
        self.assertEqual(song.website(), "www.foo")
        song["contact"] = "https://www.foo.org"
        self.assertEqual(song.website(), "https://www.foo.org")
        song["website"] = "foo\nhttps://another.com"
        self.assertEqual(song.website(), "foo")

        song = AudioFile({"artist": "Artist", "album": "Album"})
        for value in list(song.values()):
            self.assertTrue(value in song.website())
        song["labelid"] = "QL-12345"
        self.assertFalse(song["artist"] in song.website())
        self.assertTrue(song["labelid"] in song.website())

    def test_lyric_filename(self):
        song = AudioFile()
        song["~filename"] = fsnative("filename")
        self.assertTrue(is_fsnative(song.lyric_filename))
        song["title"] = "Title"
        song["artist"] = "Artist"
        self.assertTrue(is_fsnative(song.lyric_filename))
        song["lyricist"] = "Lyricist"
        self.assertTrue(is_fsnative(song.lyric_filename))

    def test_sanitize(self):
        q = AudioFile(quux)
        b = AudioFile(bar_1_1)
        q.sanitize()
        b.pop('~filename')
        self.assertRaises(ValueError, b.sanitize)
        n = AudioFile({"artist": "foo\0bar", "title": "baz\0",
                       "~filename": fsnative("whatever")})
        n.sanitize()
        self.assertEqual(n["artist"], "foo\nbar")
        self.assertEqual(n["title"], "baz")

    def test_performers(self):
        q = AudioFile([("performer:vocals", "A"), ("performer:guitar", "B"),
                       ("performer", "C")])
        self.assertEqual(set(q.list("~performers")), {"A", "B", "C"})
        self.assertEqual(set(q.list("~performers:roles")),
                             {"A (Vocals)", "B (Guitar)", "C"})

    def test_performers_multi_value(self):
        q = AudioFile([
            ("performer:vocals", "X\nA\nY"),
            ("performer:guitar", "Y\nB\nA"),
            ("performer", "C\nF\nB\nA"),
        ])

        self.assertEqual(
            set(q.list("~performer")), {"A", "B", "C", "F", "X", "Y"})

        self.assertEqual(
            set(q.list("~performer:roles")), {
                    "A (Guitar, Vocals)",
                    "C",
                    "B (Guitar)",
                    "X (Vocals)",
                    "Y (Guitar, Vocals)",
                    "F",
                })

    def test_people(self):
        q = AudioFile([("performer:vocals", "A"), ("performer:guitar", "B"),
                       ("performer", "C"), ("arranger", "A"),
                       ("albumartist", "B"), ("artist", "C")])
        self.assertEqual(q.list("~people"), ["C", "B", "A"])
        self.assertEqual(q.list("~people:roles"),
                         ["C", "B (Guitar)", "A (Arrangement, Vocals)"])

    def test_people_mix(self):
        q = AudioFile([
            ("performer:arrangement", "A"),
            ("arranger", "A"),
            ("performer", "A"),
            ("performer:foo", "A"),
        ])
        self.assertEqual(q.list("~people"), ["A"])
        self.assertEqual(q.list("~people:roles"),
                             ["A (Arrangement, Arrangement, Foo)"])

    def test_people_multi_value(self):
        q = AudioFile([
            ("arranger", "A\nX"),
            ("performer", "A\nY"),
            ("performer:foo", "A\nX"),
        ])

        self.assertEqual(q.list("~people"), ["A", "Y", "X"])
        self.assertEqual(
            q.list("~people:roles"),
            ["A (Arrangement, Foo)", "Y", "X (Arrangement, Foo)"])

    def test_people_individuals(self):
        q = AudioFile({"artist": "A\nX", "albumartist": "Various Artists"})
        self.assertEqual(q.list("~people:real"), ["A", "X"])

        lonely = AudioFile({"artist": "various artists", "title": "blah"})
        self.assertEqual(lonely.list("~people:real"),
                             ["various artists"])

        lots = AudioFile({"artist": "Various Artists", "albumartist": "V.A."})
        self.assertEqual(lots.list("~people:real"),
                             ["Various Artists"])

    def test_peoplesort(self):
        q = AudioFile([("performer:vocals", "The A"),
                       ("performersort:vocals", "A, The"),
                       ("performer:guitar", "The B"),
                       ("performersort:guitar", "B, The"),
                       ("performer", "The C"),
                       ("performersort", "C, The"),
                       ("albumartist", "The B"),
                       ("albumartistsort", "B, The")])
        self.assertEqual(q.list("~peoplesort"),
                             ["B, The", "C, The", "A, The"])
        self.assertEqual(q.list("~peoplesort:roles"),
                             ["B, The (Guitar)", "C, The", "A, The (Vocals)"])

    def test_to_dump(self):
        dump = bar_1_1.to_dump()
        num = len(set(bar_1_1.keys()) | INTERN_NUM_DEFAULT)
        self.assertEqual(dump.count("\n"), num + 2)
        for key, value in list(bar_1_1.items()):
            self.assertTrue(key in dump)
            self.assertTrue(value in dump)
        for key in INTERN_NUM_DEFAULT:
            self.assertTrue(key in dump)

        n = AudioFile()
        n.from_dump(dump)
        self.assertTrue(set(dump.split("\n")) == set(n.to_dump().split("\n")))

    def test_to_dump_long(self):
        b = AudioFile(bar_1_1)
        b["~#length"] = 200000000000
        dump = b.to_dump()
        num = len(set(bar_1_1.keys()) | INTERN_NUM_DEFAULT)
        self.assertEqual(dump.count("\n"), num + 2)

        n = AudioFile()
        n.from_dump(dump)
        self.assertTrue(set(dump.split("\n")) == set(n.to_dump().split("\n")))

    def test_to_dump_unicode(self):
        b = AudioFile(bar_1_1)
        b["öäü"] = "öäü"
        dump = b.to_dump()
        n = AudioFile()
        n.from_dump(dump)
        self.assertEqual(n["öäü"], "öäü")

    def test_add(self):
        song = AudioFile()
        self.assertFalse("foo" in song)
        song.add("foo", "bar")
        self.assertEqual(song["foo"], "bar")
        song.add("foo", "another")
        self.assertEqual(song.list("foo"), ["bar", "another"])

    def test_remove(self):
        song = AudioFile()
        song.add("foo", "bar")
        song.add("foo", "another")
        song.add("foo", "one more")
        song.remove("foo", "another")
        self.assertEqual(song.list("foo"), ["bar", "one more"])
        song.remove("foo", "bar")
        self.assertEqual(song.list("foo"), ["one more"])
        song.remove("foo", "one more")
        self.assertFalse("foo" in song)

    def test_remove_unknown(self):
        song = AudioFile()
        song.add("foo", "bar")
        song.remove("foo", "not in list")
        song.remove("nope")
        self.assertEqual(song.list("foo"), ["bar"])

    def test_remove_all(self):
        song = AudioFile()
        song.add("foo", "bar")
        song.add("foo", "another")
        song.add("foo", "one more")
        song.remove("foo")
        self.assertFalse("foo" in song)

    def test_remove_empty(self):
        song = AudioFile()
        song.add("foo", "")
        song.remove("foo", "")
        self.assertFalse("foo" in song)

    def test_change(self):
        song = AudioFile()
        song.add("foo", "bar")
        song.add("foo", "another")
        song.change("foo", "bar", "one more")
        self.assertEqual(song.list("foo"), ["one more", "another"])
        song.change("foo", "does not exist", "finally")
        self.assertEqual(song["foo"], "finally")
        song.change("foo", "finally", "we're done")
        self.assertEqual(song["foo"], "we're done")

    def test_bookmarks_none(self):
        self.assertEqual([], AudioFile().bookmarks)

    def test_bookmarks_simple(self):
        af = AudioFile({"~bookmark": "1:20 Mark 1"})
        self.assertEqual([(80, "Mark 1")], af.bookmarks)

    def test_bookmarks_two(self):
        af = AudioFile({"~bookmark": "1:40 Mark 2\n1:20 Mark 1"})
        self.assertEqual([(80, "Mark 1"), (100, "Mark 2")], af.bookmarks)

    def test_bookmark_invalid(self):
        af = AudioFile({"~bookmark": ("Not Valid\n1:40 Mark 2\n"
                                      "-20 Not Valid 2\n1:20 Mark 1")})
        self.assertEqual(
            [(80, "Mark 1"), (100, "Mark 2"), (-1, "Not Valid"),
             (-1, "-20 Not Valid 2")], af.bookmarks)

    def test_set_bookmarks_none(self):
        af = AudioFile({"bookmark": "foo"})
        af.bookmarks = []
        self.assertEqual([], AudioFile().bookmarks)
        self.assertFalse("~bookmark" in af)

    def test_set_bookmarks_simple(self):
        af = AudioFile()
        af.bookmarks = [(120, "A mark"), (140, "Mark twain")]
        self.assertEqual(af["~bookmark"], "2:00 A mark\n2:20 Mark twain")

    def test_set_bookmarks_invalid_value(self):
        self.assertRaises(
            ValueError, setattr, AudioFile(), 'bookmarks', "huh?")

    def test_set_bookmarks_invalid_time(self):
        self.assertRaises(
            TypeError, setattr, AudioFile(), 'bookmarks', [("notint", "!")])

    def test_set_bookmarks_unrealistic_time(self):
        self.assertRaises(
            ValueError, setattr, AudioFile(), 'bookmarks', [(-1, "!")])

    def test_album_key(self):
        album_key_tests = [
            ({}, ('', '', '')),
            ({'album': 'foo'}, (('foo',), '', '')),
            ({'labelid': 'foo'}, ('', '', 'foo')),
            ({'musicbrainz_albumid': 'foo'}, ('', '', 'foo')),
            ({'album': 'foo', 'labelid': 'bar'}, (('foo',), '', 'bar')),
            ({'album': 'foo', 'labelid': 'bar', 'musicbrainz_albumid': 'quux'},
                (('foo',), '', 'bar')),
            ({'albumartist': 'a'}, ('', ('a',), '')),
            ]
        for tags, expected in album_key_tests:
            afile = AudioFile(**tags)
            afile.sanitize(fsnative('/dir/fn'))
            self.assertEqual(afile.album_key, expected)

    def test_eq_ne(self):
        self.assertFalse(AudioFile({"a": "b"}) == AudioFile({"a": "b"}))
        self.assertTrue(AudioFile({"a": "b"}) != AudioFile({"a": "b"}))

    def test_invalid_fs_encoding(self):
        # issue 798
        a = AudioFile()
        if os.name != "nt":
            a["~filename"] = "/\xf6\xe4\xfc/\xf6\xe4\xfc.ogg" # latin 1 encoded
            a.sort_by_func("~filename")(a)
            a.sort_by_func("~basename")(a)
        else:
            # windows
            a["~filename"] = "/\xf6\xe4\xfc/\xf6\xe4\xfc.ogg".decode("latin-1")
            a.sort_by_func("~filename")(a)
            a.sort_by_func("~basename")(a)
            a.sort_by_func("~dirname")(a)

    def test_sort_cache(self):
        copy = AudioFile(bar_1_1)

        sort_1 = tuple(copy.sort_key)
        copy["title"] = copy["title"] + "something"
        sort_2 = tuple(copy.sort_key)
        self.assertNotEqual(sort_1, sort_2)

        album_sort_1 = tuple(copy.album_key)
        copy["album"] = copy["album"] + "something"
        sort_3 = tuple(copy.sort_key)
        self.assertNotEqual(sort_2, sort_3)

        album_sort_2 = tuple(copy.album_key)
        self.assertNotEqual(album_sort_1, album_sort_2)

    def test_cache_attributes(self):
        x = AudioFile()
        x.multisong = not x.multisong
        x["a"] = "b" # clears cache
        # attribute should be unchanged
        self.assertNotEqual(AudioFile().multisong, x.multisong)

    def test_sort_func(self):
        tags = [lambda s: s("foo"), "artistsort", "albumsort",
                "~filename", "~format", "discnumber", "~#track"]

        for tag in tags:
            f = AudioFile.sort_by_func(tag)
            f(bar_1_1)
            f(bar_1_2)
            f(bar_2_1)

    def test_uri(self):
        # On windows where we have unicode paths (windows encoding is utf-16)
        # we need to encode to utf-8 first, then escape.
        # On linux we take the byte stream and escape it.
        # see g_filename_to_uri

        if os.name == "nt":
            f = AudioFile({"~filename": "/\xf6\xe4.mp3", "title": "win"})
            self.assertEqual(f("~uri"), "file:///%C3%B6%C3%A4.mp3")
        else:
            f = AudioFile({"~filename": "/\x87\x12.mp3", "title": "linux"})
            self.assertEqual(f("~uri"), "file:///%87%12.mp3")

    def tearDown(self):
        os.unlink(quux["~filename"])


class Tdecode_value(TestCase):

    def test_main(self):
        self.assertEqual(decode_value("~#foo", 0.25), "0.25")
        self.assertEqual(decode_value("~#foo", 4), "4")
        self.assertEqual(decode_value("~#foo", "bar"), "bar")
        self.assertTrue(isinstance(decode_value("~#foo", "bar"), str))
        path = fsnative("/foobar")
        self.assertEqual(decode_value("~filename", path), fsdecode(path))


class Treplay_gain(TestCase):

    # -6dB is approximately equal to half magnitude
    minus_6db = 0.501187234

    def setUp(self):
        self.rg_data = {"replaygain_album_gain": "-1.00 dB",
                        "replaygain_album_peak": "1.1",
                        "replaygain_track_gain": "+1.0000001 dB",
                        "replaygain_track_peak": "0.9"}
        self.song = AudioFile(self.rg_data)
        self.no_rg_song = AudioFile()

    def test_no_rg_song(self):
        scale = self.no_rg_song.replay_gain(["track"], 0, -6.0)
        self.assertAlmostEqual(scale, self.minus_6db)

        scale = self.no_rg_song.replay_gain(["track"], +10, +10)
        self.assertEqual(scale, 1.0)

        scale = self.no_rg_song.replay_gain(["track"], -16.0, +10)
        self.assertAlmostEqual(scale, self.minus_6db)

    def test_nogain(self):
        self.assertEqual(self.song.replay_gain(["none", "track"]), 1)

    def test_fallback_track(self):
        del(self.song["replaygain_track_gain"])
        self.assertAlmostEqual(
            self.song.replay_gain(["track"], 0, -6.0), self.minus_6db)

    def test_fallback_album(self):
        del(self.song["replaygain_album_gain"])
        self.assertAlmostEqual(
            self.song.replay_gain(["album"], 0, -6.0), self.minus_6db)

    def test_fallback_and_preamp(self):
        del(self.song["replaygain_track_gain"])
        self.assertEqual(self.song.replay_gain(["track"], 9, -9), 1)

    def test_preamp_track(self):
        self.assertAlmostEqual(
            self.song.replay_gain(["track"], -7.0, 0), self.minus_6db)

    def test_preamp_album(self):
        self.assertAlmostEqual(
            self.song.replay_gain(["album"], -5.0, 0), self.minus_6db)

    def test_preamp_clip(self):
        # Make sure excess pre-amp won't clip a track (with peak data)
        self.assertAlmostEqual(
            self.song.replay_gain(["track"], 12.0, 0), 1.0 / 0.9)

    def test_trackgain(self):
        self.assertTrue(self.song.replay_gain(["track"]) > 1)

    def test_albumgain(self):
        self.assertTrue(self.song.replay_gain(["album"]) < 1)

    def test_invalid(self):
        self.song["replaygain_album_gain"] = "fdsodgbdf"
        self.assertEqual(self.song.replay_gain(["album"]), 1)

    def test_track_fallback(self):
        radio_rg = self.song.replay_gain(["track"])
        del(self.song["replaygain_album_gain"])
        del(self.song["replaygain_album_peak"])
        # verify defaulting to track when album is present
        self.assertAlmostEqual(
            self.song.replay_gain(["album", "track"]), radio_rg)

    def test_numeric_rg_tags(self):
        """"Tests fully-numeric (ie no "db") RG tags.  See Issue 865"""
        self.assertTrue(self.song("replaygain_album_gain"), "-1.00 db")
        for key, exp in list(self.rg_data.items()):
            # Hack the nasties off and produce the "real" expected value
            exp = float(exp.split(" ")[0])
            # Compare as floats. Seems fairer.
            album_rg = self.song("~#%s" % key)
            try:
                val = float(album_rg)
            except ValueError:
                self.fail("Invalid %s returned: %s" % (key, album_rg))
            self.assertAlmostEqual(
                val, exp, places=5,
                msg="%s should be %s not %s" % (key, exp, val))
