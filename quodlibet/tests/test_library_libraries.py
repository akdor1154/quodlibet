# -*- coding: utf-8 -*-
from gi.repository import Gtk

import os
import shutil
from quodlibet import config
from quodlibet.util import connect_obj
from quodlibet.formats import AudioFile

from tests import TestCase, DATA_DIR, mkstemp
from .helper import capture_output

from quodlibet.library.libraries import *


class Fake(int):
    def __init__(self, _):
        self.key = int(self)


def Frange(*args):
    return list(map(Fake, list(range(*args))))


class FakeSong(Fake):
    def list(self, tag):
        # Turn tag_values into a less-than query, for testing.
        if tag <= self:
            return []
        else:
            return [int(self)]

    def rename(self, newname):
        self.key = newname


class AlbumSong(AudioFile):
    """A mock AudioFile belong to one of three albums,
    based on a single number"""
    def __init__(self, num, album=None):
        super(AlbumSong, self).__init__()
        self["~filename"] = "file_%d.mp3" % (num + 1)
        self["title"] = "Song %d" % (num + 1)
        self["artist"] = "Fakeman"
        if album is None:
            self["album"] = "Album %d" % (num % 3 + 1)
        else:
            self["album"] = album
        self["labelid"] = self["album"]


class FakeSongFile(FakeSong):
    _valid = True
    _exists = True
    _mounted = True

    @property
    def mountpoint(self):
        return "/" if self._mounted else "/FAKE"

    def valid(self):
        return self._valid

    def exists(self):
        return self._exists

    def reload(self):
        if self._exists:
            self._valid = True
        else:
            raise IOError("doesn't exist")

    def mounted(self):
        return self._mounted


# Custom range functions, to generate lists of song-like objects
def FSFrange(*args):
    return list(map(FakeSongFile, list(range(*args))))


def FSrange(*args):
    return list(map(FakeSong, list(range(*args))))


def ASrange(*args):
    return list(map(AlbumSong, list(range(*args))))


class TLibrary(TestCase):
    Fake = Fake
    Frange = staticmethod(Frange)
    Library = Library

    def setUp(self):
        self.library = self.Library()
        self.added = []
        self.changed = []
        self.removed = []

        connect_obj(self.library, 'added', list.extend, self.added)
        connect_obj(self.library, 'changed', list.extend, self.changed)
        connect_obj(self.library, 'removed', list.extend, self.removed)

    def test_add(self):
        self.library.add(self.Frange(12))
        self.assertEqual(self.added, self.Frange(12))
        del(self.added[:])
        self.library.add(self.Frange(12, 24))
        self.assertEqual(self.added, self.Frange(12, 24))

    def test_remove(self):
        self.library.add(self.Frange(10))
        self.assertTrue(self.library.remove(self.Frange(3, 6)))
        self.assertEqual(self.removed, self.Frange(3, 6))

        # Neither the objects nor their keys should be present.
        self.assertFalse(self.Fake(3) in self.library)
        self.assertTrue(self.Fake(6) in self.library)
        self.assertFalse(3 in self.library)
        self.assertTrue(6 in self.library)

    def test_remove_when_not_present(self):
        self.assertFalse(self.library.remove([self.Fake(12)]))

    def test_changed(self):
        self.library.add(self.Frange(10))
        self.library.changed(self.Frange(5))
        while Gtk.events_pending():
            Gtk.main_iteration()
        self.assertEqual(self.changed, self.Frange(5))

    def test_changed_not_present(self):
        self.library.add(self.Frange(10))
        self.library.changed(self.Frange(2, 20, 3))
        while Gtk.events_pending():
            Gtk.main_iteration()
        self.assertEqual(set(self.changed), {2, 5, 8})

    def test_changed_none_present(self):
        self.library.changed(self.Frange(5))
        while Gtk.events_pending():
            Gtk.main_iteration()

    def test___iter__(self):
        self.library.add(self.Frange(10))
        self.assertEqual(sorted(list(self.library)), self.Frange(10))

    def test___iter___empty(self):
        self.assertFalse(list(self.library))

    def test___len__(self):
        self.assertEqual(len(self.library), 0)
        self.library.add(self.Frange(10))
        self.assertEqual(len(self.library), 10)
        self.library.remove(self.Frange(3))
        self.assertEqual(len(self.library), 7)

    def test___getitem__(self):
        self.library.add(self.Frange(10))
        self.assertEqual(self.library[5], 5)
        new = self.Fake(12)
        new.key = 100
        self.library.add([new])
        self.assertEqual(self.library[100], 12)
        self.assertFalse(12 in self.library)

    def test___getitem___not_present(self):
        self.library.add(self.Frange(10))
        self.assertRaises(KeyError, self.library.__getitem__, 12)

    def test___contains__(self):
        self.library.add(self.Frange(10))
        new = self.Fake(12)
        new.key = 100
        self.library.add([new])
        for value in [0, 1, 2, 6, 9, 100, new]:
            # 0, 1, 2, 6, 9: all added by self.Frange
            # 100: key for new
            # new: is itself present
            self.assertTrue(value in self.library, "didn't find %d" % value)

        for value in [-1, 10, 12, 101]:
            # -1, 10, 101: boundry values
            # 12: equal but non-key-equal to new
            self.assertFalse(value in self.library, "found %d" % value)

    def test_get(self):
        self.assertTrue(self.library.get(12) is None)
        self.assertTrue(self.library.get(12, "foo") == "foo")
        new = self.Fake(12)
        new.key = 100
        self.library.add([new])
        self.assertTrue(self.library.get(12) is None)
        self.assertTrue(self.library.get(100) is new)

    def test_keys(self):
        items = []
        for i in range(20):
            items.append(self.Fake(i))
            items[-1].key = i + 100
        self.library.add(items)
        self.assertEqual(sorted(self.library.keys()), list(range(100, 120)))
        self.assertEqual(sorted(self.library.keys()), list(range(100, 120)))

    def test_values(self):
        items = []
        for i in range(20):
            items.append(self.Fake(i))
            items[-1].key = i + 100
        self.library.add(items)
        self.assertEqual(sorted(self.library.values()), list(range(20)))
        self.assertEqual(sorted(self.library.values()), list(range(20)))

    def test_items(self):
        items = []
        for i in range(20):
            items.append(self.Fake(i))
            items[-1].key = i + 100
        self.library.add(items)
        expected = list(zip(list(range(100, 120)), list(range(20))))
        self.assertEqual(sorted(self.library.items()), expected)
        self.assertEqual(sorted(self.library.items()), expected)

    def test_has_key(self):
        self.assertFalse(10 in self.library)
        new = self.Fake(10)
        new.key = 20
        self.library.add([new])
        self.assertFalse(10 in self.library)
        self.assertTrue(20 in self.library)

    def tearDown(self):
        self.library.destroy()


class TPicklingMixin(TestCase):

    class PicklingMockLibrary(PicklingMixin, Library):
        """A library-like class that implements enough to test PicklingMixin"""
        def __init__(self):
            PicklingMixin.__init__(self)
            self._contents = {}
            # set up just enough of the library interface to work
            self.values = self._contents.values
            self.items = self._contents.items

        def add(self, items):
            for item in items:
                self._contents[item.key] = item

    Library = PicklingMockLibrary
    Frange = staticmethod(Frange)

    def setUp(self):
        self.library = self.Library()

    def test_save_load(self):
        fd, filename = mkstemp()
        os.close(fd)
        try:
            self.library.add(Frange(30))
            self.library.save(filename)

            library = self.Library()
            library.load(filename)
            self.assertEqual(
                sorted(self.library.items()), sorted(library.items()))
        finally:
            os.unlink(filename)


class TSongLibrary(TLibrary):
    Fake = FakeSong
    Frange = staticmethod(FSrange)
    Library = SongLibrary

    def test_rename_dirty(self):
        self.library.dirty = False
        song = FakeSong(10)
        self.library.add([song])
        self.assertTrue(self.library.dirty)
        self.library.dirty = False
        self.library.rename(song, 20)
        self.assertTrue(self.library.dirty)

    def test_rename(self):
        song = FakeSong(10)
        self.library.add([song])
        self.library.rename(song, 20)
        while Gtk.events_pending():
            Gtk.main_iteration()
        self.assertTrue(song in self.changed)
        self.assertTrue(song in self.library)
        self.assertTrue(song.key in self.library)
        self.assertEqual(song.key, 20)

    def test_rename_changed(self):
        song = FakeSong(10)
        self.library.add([song])
        changed = set()
        self.library.rename(song, 20, changed=changed)
        self.assertEqual(len(changed), 1)
        self.assertTrue(song in changed)

    def test_tag_values(self):
        self.library.add(self.Frange(30))
        del(self.added[:])
        self.assertEqual(sorted(self.library.tag_values(10)), list(range(10)))
        self.assertEqual(sorted(self.library.tag_values(0)), [])
        self.assertFalse(self.changed or self.added or self.removed)


class TFileLibrary(TLibrary):
    Fake = FakeSongFile
    Library = FileLibrary

    def test_mask_invalid_mount_point(self):
        new = self.Fake(1)
        self.library.add([new])
        self.assertFalse(self.library.masked_mount_points)
        self.assertTrue(len(self.library))
        self.library.mask("/adsadsafaf")
        self.assertFalse(self.library.masked_mount_points)
        self.library.unmask("/adsadsafaf")
        self.assertFalse(self.library.masked_mount_points)
        self.assertTrue(len(self.library))

    def test_mask_basic(self):
        new = self.Fake(1)
        self.library.add([new])
        self.assertFalse(self.library.masked_mount_points)
        self.library.mask(new.mountpoint)
        self.assertEqual(self.library.masked_mount_points,
                             [new.mountpoint])
        self.assertFalse(len(self.library))
        self.assertEqual(self.library.get_masked(new.mountpoint), [new])
        self.assertTrue(self.library.masked(new))
        self.library.unmask(new.mountpoint)
        self.assertTrue(len(self.library))
        self.assertEqual(self.library.get_masked(new.mountpoint), [])

    def test_remove_masked(self):
        new = self.Fake(1)
        self.library.add([new])
        self.library.mask(new.mountpoint)
        self.assertTrue(self.library.masked_mount_points)
        self.library.remove_masked(new.mountpoint)
        self.assertFalse(self.library.masked_mount_points)

    def test_content_masked(self):
        new = self.Fake(100)
        new._mounted = False
        self.assertFalse(self.library.get_content())
        self.library._load_init([new])
        self.assertTrue(self.library.masked(new))
        self.assertTrue(self.library.get_content())

    def test_init_masked(self):
        new = self.Fake(100)
        new._mounted = False
        self.library._load_init([new])
        self.assertFalse(list(self.library.items()))
        self.assertTrue(self.library.masked(new))

    def test_load_init_nonmasked(self):
        new = self.Fake(200)
        new._mounted = True
        self.library._load_init([new])
        self.assertEqual(list(self.library.values()), [new])

    def test_reload(self):
        new = self.Fake(200)
        self.library.add([new])
        changed = set()
        removed = set()
        self.library.reload(new, changed=changed, removed=removed)
        self.assertTrue(new in changed)
        self.assertFalse(removed)


class TSongFileLibrary(TSongLibrary):
    Fake = FakeSongFile
    Frange = staticmethod(FSFrange)
    Library = SongFileLibrary

    def test__load_exists_invalid(self):
        new = self.Fake(100)
        new._valid = False
        changed, removed = self.library._load_item(new)
        self.assertFalse(removed)
        self.assertTrue(changed)
        self.assertTrue(new._valid)
        self.assertTrue(new in self.library)

    def test__load_not_exists(self):
        new = self.Fake(100)
        new._valid = False
        new._exists = False
        changed, removed = self.library._load_item(new)
        self.assertFalse(removed)
        self.assertFalse(changed)
        self.assertFalse(new._valid)
        self.assertFalse(new in self.library)

    def test__load_error_during_reload(self):
        try:
            from quodlibet import util
            print_exc = util.print_exc
            util.print_exc = lambda *args, **kwargs: None
            new = self.Fake(100)

            def error():
                raise IOError
            new.reload = error
            new._valid = False
            changed, removed = self.library._load_item(new)
            self.assertTrue(removed)
            self.assertFalse(changed)
            self.assertFalse(new._valid)
            self.assertFalse(new in self.library)
        finally:
            util.print_exc = print_exc

    def test__load_not_mounted(self):
        new = self.Fake(100)
        new._valid = False
        new._exists = False
        new._mounted = False
        changed, removed = self.library._load_item(new)
        self.assertFalse(removed)
        self.assertFalse(changed)
        self.assertFalse(new._valid)
        self.assertFalse(new in self.library)
        self.assertTrue(self.library.masked(new))

    def __get_file(self):
        fd, filename = mkstemp(".flac")
        os.close(fd)
        shutil.copy(os.path.join(DATA_DIR, 'empty.flac'), filename)
        return filename

    def test_add_filename(self):
        config.init()
        try:
            filename = self.__get_file()
            ret = self.library.add_filename(filename)
            self.assertTrue(ret)
            self.assertEqual(1, len(self.library))
            self.assertEqual(len(self.added), 1)
            ret = self.library.add_filename(filename)
            self.assertTrue(ret)
            self.assertEqual(len(self.added), 1)
            os.unlink(filename)

            filename = self.__get_file()
            ret = self.library.add_filename(filename, add=False)
            self.assertTrue(ret)
            self.assertFalse(ret in self.library)
            self.assertEqual(len(self.added), 1)
            self.library.add([ret])
            self.assertTrue(ret in self.library)
            self.assertEqual(len(self.added), 2)
            self.assertEqual(2, len(self.library))
            os.unlink(filename)

            with capture_output():
                ret = self.library.add_filename("")
            self.assertFalse(ret)
            self.assertEqual(len(self.added), 2)
            self.assertEqual(2, len(self.library))

        finally:
            config.quit()

    def test_add_filename_normalize_path(self):
        if not os.name == "nt":
            return

        config.init()
        filename = self.__get_file()

        # create a equivalent path different from the original one
        if filename.upper() == filename:
            other = filename.lower()
        else:
            other = filename.upper()

        song = self.library.add_filename(filename)
        other_song = self.library.add_filename(other)
        self.assertTrue(song is other_song)
        os.unlink(filename)
        config.quit()


class TAlbumLibrary(TestCase):
    Fake = FakeSong
    Frange = staticmethod(ASrange)
    UnderlyingLibrary = Library

    def setUp(self):
        self.underlying = self.UnderlyingLibrary()
        self.added = []
        self.changed = []
        self.removed = []

        self._sigs = [
            connect_obj(self.underlying, 'added', list.extend, self.added),
            connect_obj(self.underlying,
                'changed', list.extend, self.changed),
            connect_obj(self.underlying,
                'removed', list.extend, self.removed),
        ]

        self.library = AlbumLibrary(self.underlying)

        # Populate for every test
        self.underlying.add(self.Frange(12))

    def tearDown(self):
        for s in self._sigs:
            self.underlying.disconnect(s)
        self.underlying.destroy()
        self.library.destroy()

    def test_get(self):
        key = self.underlying.get("file_1.mp3").album_key
        self.assertEqual(self.library.get(key).title, "Album 1")
        album = self.library.get(key)
        self.assertEqual(album.key, key)
        self.assertEqual(len(album.songs), 4)

        key = self.underlying.get("file_2.mp3").album_key
        self.assertEqual(self.library.get(key).title, "Album 2")

    def test_getitem(self):
        key = self.underlying.get("file_4.mp3").album_key
        self.assertEqual(self.library[key].key, key)

    def test_keys(self):
        self.assertTrue(len(list(self.library.keys())), 3)

    def test_has_key(self):
        key = self.underlying.get("file_1.mp3").album_key
        self.assertTrue(key in self.library)

    def test_misc_collection(self):
        self.assertTrue(iter(self.library.values()))
        self.assertTrue(iter(self.library.items()))

    def test_items(self):
        self.assertEqual(len(list(self.library.items())), 3)

    def test_items_2(self):
        albums = list(self.library.values())
        self.assertEqual(len(albums), 3)
        songs = list(self.underlying._contents.values())
        # Make sure "all the songs' albums" == "all the albums", roughly
        self.assertEqual({a.key for a in albums},
                             {s.album_key for s in songs})

    def test_remove(self):
        key = self.underlying.get("file_1.mp3").album_key
        songs = self.underlying._contents

        # Remove all songs in Album 1
        for i in range(1, 12, 3):
            song = songs["file_%d.mp3" % i]
            self.underlying.remove([song])

        # Album 1 is all gone...
        self.assertEqual(self.library.get(key), None)

        # ...but Album 2 is fine
        key = self.underlying.get("file_2.mp3").album_key
        album2 = self.library[key]
        self.assertEqual(album2.key, key)
        self.assertEqual(len(album2.songs), 4)

    def test_misc(self):
        # It shouldn't implement FileLibrary etc
        self.assertFalse(getattr(self.library, "filename", None))


class TAlbumLibrarySignals(TestCase):
    def setUp(self):
        lib = SongLibrary()
        received = []

        def listen(name, items):
            received.append(name)

        self._sigs = [
            connect_obj(lib, 'added', listen, 'added'),
            connect_obj(lib, 'changed', listen, 'changed'),
            connect_obj(lib, 'removed', listen, 'removed'),
        ]

        albums = lib.albums
        self._asigs = [
            connect_obj(albums, 'added', listen, 'a_added'),
            connect_obj(albums, 'changed', listen, 'a_changed'),
            connect_obj(albums, 'removed', listen, 'a_removed'),
        ]

        self.lib = lib
        self.albums = albums
        self.received = received

    def test_add_one(self):
        self.lib.add([AlbumSong(1)])
        self.assertEqual(self.received, ["added", "a_added"])

    def test_add_two_same(self):
        self.lib.add([AlbumSong(1, "a1")])
        self.lib.add([AlbumSong(5, "a1")])
        self.assertEqual(self.received,
            ["added", "a_added", "added", "a_changed"])

    def test_remove(self):
        songs = [AlbumSong(1, "a1"), AlbumSong(2, "a1"), AlbumSong(4, "a2")]
        self.lib.add(songs)
        self.lib.remove(songs[:2])
        self.assertEqual(self.received,
            ["added", "a_added", "removed", "a_removed"])

    def test_change(self):
        songs = [AlbumSong(1, "a1"), AlbumSong(2, "a1"), AlbumSong(4, "a2")]
        self.lib.add(songs)
        self.lib.changed(songs)
        self.assertEqual(self.received,
            ["added", "a_added", "changed", "a_changed"])

    def tearDown(self):
        for s in self._asigs:
            self.albums.disconnect(s)
        for s in self._sigs:
            self.lib.disconnect(s)
        self.lib.destroy()
