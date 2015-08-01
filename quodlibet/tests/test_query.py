# -*- encoding: utf-8 -*-
from tests import TestCase

from quodlibet import config
from quodlibet.query import Query, QueryType
from quodlibet.query import _match as match
from quodlibet.formats import AudioFile


class TQuery_is_valid(TestCase):
    def test_re(self):
        self.assertTrue(Query.is_valid('t = /an re/'))
        self.assertTrue(Query.is_valid('t = /an re/c'))
        self.assertTrue(Query.is_valid('t = /an\\/re/'))
        self.assertFalse(Query.is_valid('t = /an/re/'))
        self.assertTrue(Query.is_valid('t = /aaa/lsic'))
        self.assertFalse(Query.is_valid('t = /aaa/icslx'))

    def test_str(self):
        self.assertTrue(Query.is_valid('t = "a str"'))
        self.assertTrue(Query.is_valid('t = "a str"c'))
        self.assertTrue(Query.is_valid('t = "a\\"str"'))
        # there's no equivalent failure for strings since 'str"' would be
        # read as a set of modifiers

    def test_tag(self):
        self.assertTrue(Query.is_valid('t = tag'))
        self.assertTrue(Query.is_valid('t = !tag'))
        self.assertTrue(Query.is_valid('t = |(tag, bar)'))
        self.assertTrue(Query.is_valid('t = a"tag"'))
        self.assertFalse(Query.is_valid('t = a, tag'))

    def test_empty(self):
        self.assertTrue(Query.is_valid(''))
        self.assertTrue(Query.is_parsable(''))
        self.assertTrue(Query(''))

    def test_emptylist(self):
        self.assertFalse(Query.is_valid("a = &()"))
        self.assertFalse(Query.is_valid("a = |()"))
        self.assertFalse(Query.is_valid("|()"))
        self.assertFalse(Query.is_valid("&()"))

    def test_nonsense(self):
        self.assertFalse(Query.is_valid('a string'))
        self.assertFalse(Query.is_valid('t = #(a > b)'))
        self.assertFalse(Query.is_valid("=a= = /b/"))
        self.assertFalse(Query.is_valid("a = &(/b//"))
        self.assertFalse(Query.is_valid("(a = &(/b//)"))

    def test_trailing(self):
        self.assertFalse(Query.is_valid('t = /an re/)'))
        self.assertFalse(Query.is_valid('|(a, b = /a/, c, d = /q/) woo'))

    def test_not(self):
        self.assertTrue(Query.is_valid('t = !/a/'))
        self.assertTrue(Query.is_valid('t = !!/a/'))
        self.assertTrue(Query.is_valid('!t = "a"'))
        self.assertTrue(Query.is_valid('!!t = "a"'))
        self.assertTrue(Query.is_valid('t = !|(/a/, !"b")'))
        self.assertTrue(Query.is_valid('t = !!|(/a/, !"b")'))
        self.assertTrue(Query.is_valid('!|(t = /a/)'))

    def test_taglist(self):
        self.assertTrue(Query.is_valid('a, b = /a/'))
        self.assertTrue(Query.is_valid('a, b, c = |(/a/)'))
        self.assertTrue(Query.is_valid('|(a, b = /a/, c, d = /q/)'))
        self.assertFalse(Query.is_valid('a = /a/, b'))

    def test_andor(self):
        self.assertTrue(Query.is_valid('a = |(/a/, /b/)'))
        self.assertTrue(Query.is_valid('a = |(/b/)'))
        self.assertTrue(Query.is_valid('|(a = /b/, c = /d/)'))

        self.assertTrue(Query.is_valid('a = &(/a/, /b/)'))
        self.assertTrue(Query.is_valid('a = &(/b/)'))
        self.assertTrue(Query.is_valid('&(a = /b/, c = /d/)'))

    def test_numcmp(self):
        self.assertTrue(Query.is_valid("#(t < 3)"))
        self.assertTrue(Query.is_valid("#(t <= 3)"))
        self.assertTrue(Query.is_valid("#(t > 3)"))
        self.assertTrue(Query.is_valid("#(t >= 3)"))
        self.assertTrue(Query.is_valid("#(t = 3)"))
        self.assertTrue(Query.is_valid("#(t != 3)"))

        self.assertFalse(Query.is_valid("#(t !> 3)"))
        self.assertFalse(Query.is_valid("#(t >> 3)"))

    def test_trinary(self):
        self.assertTrue(Query.is_valid("#(2 < t < 3)"))
        self.assertTrue(Query.is_valid("#(2 >= t > 3)"))
        # useless, but valid
        self.assertTrue(Query.is_valid("#(5 > t = 2)"))

    def test_list(self):
        self.assertTrue(Query.is_valid("#(t < 3, t > 9)"))
        self.assertTrue(Query.is_valid("t = &(/a/, /b/)"))
        self.assertTrue(Query.is_valid("s, t = |(/a/, /b/)"))
        self.assertTrue(Query.is_valid("|(t = /a/, s = /b/)"))

    def test_nesting(self):
        self.assertTrue(Query.is_valid("|(s, t = &(/a/, /b/),!#(2 > q > 3))"))


class TQuery(TestCase):

    def setUp(self):
        config.init()
        self.s1 = AudioFile(
            {"album": "I Hate: Tests", "artist": "piman", "title": "Quuxly",
             "version": "cake mix", "~filename": "/dir1/foobar.ogg"})
        self.s2 = AudioFile(
            {"album": "Foo the Bar", "artist": "mu", "title": "Rockin' Out",
             "~filename": "/dir2/something.mp3", "tracknumber": "12/15"})

        self.s3 = AudioFile(
            {"artist": "piman\nmu",
             "~filename": "/test/\xc3\xb6\xc3\xa4\xc3\xbc/fo\xc3\xbc.ogg"})
        self.s4 = AudioFile({"title": "Ångström", "utf8": "Ångström"})
        self.s5 = AudioFile({"title": "oh&blahhh", "artist": "!ohno"})

    def tearDown(self):
        config.quit()

    def test_repr(self):
        query = Query("foo = bar", [])
        self.assertEqual(
            repr(query),
            "<Query string=u'foo = bar' type=QueryType.VALID star=[]>")

        query = Query("bar", ["foo"])
        self.assertEqual(
            repr(query),
            "<Query string=u'&(/bar/d)' type=QueryType.TEXT star=['foo']>")

    def test_2007_07_27_synth_search(self):
        song = AudioFile({"~filename": "foo/64K/bar.ogg"})
        query = Query("~dirname = !64K")
        self.assertFalse(query.search(song), "%r, %r" % (query, song))

    def test_empty(self):
        self.assertFalse(Query("foobar = /./").search(self.s1))

    def test_gte(self):
        self.assertTrue(Query("#(track >= 11)").search(self.s2))

    def test_re(self):
        for s in ["album = /i hate/", "artist = /pi*/", "title = /x.y/"]:
            self.assertTrue(Query(s).search(self.s1))
            self.assertFalse(Query(s).search(self.s2))
        f = Query("artist = /mu|piman/").search
        self.assertTrue(f(self.s1))
        self.assertTrue(f(self.s2))

    def test_not(self):
        for s in ["album = !hate", "artist = !pi"]:
            self.assertFalse(Query(s).search(self.s1))
            self.assertTrue(Query(s).search(self.s2))

    def test_abbrs(self):
        for s in ["b = /i hate/", "a = /pi*/", "t = /x.y/"]:
            self.assertTrue(Query(s).search(self.s1))
            self.assertFalse(Query(s).search(self.s2))

    def test_str(self):
        for k in list(self.s2.keys()):
            v = self.s2[k]
            self.assertTrue(Query('%s = "%s"' % (k, v)).search(self.s2))
            self.assertFalse(Query('%s = !"%s"' % (k, v)).search(self.s2))

    def test_numcmp(self):
        self.assertFalse(Query("#(track = 0)").search(self.s1))
        self.assertFalse(Query("#(notatag = 0)").search(self.s1))
        self.assertTrue(Query("#(track = 12)").search(self.s2))

    def test_trinary(self):
        self.assertTrue(Query("#(11 < track < 13)").search(self.s2))
        self.assertTrue(Query("#(11 < track <= 12)").search(self.s2))
        self.assertTrue(Query("#(12 <= track <= 12)").search(self.s2))
        self.assertTrue(Query("#(12 <= track < 13)").search(self.s2))
        self.assertTrue(Query("#(13 > track > 11)").search(self.s2))
        self.assertTrue(Query("#(20 > track < 20)").search(self.s2))

    def test_not_2(self):
        for s in ["album = !/i hate/", "artist = !/pi*/", "title = !/x.y/"]:
            self.assertTrue(Query(s).search(self.s2))
            self.assertFalse(Query(s).search(self.s1))

    def test_case(self):
        self.assertTrue(Query("album = /i hate/").search(self.s1))
        self.assertTrue(Query("album = /I Hate/").search(self.s1))
        self.assertTrue(Query("album = /i Hate/").search(self.s1))
        self.assertTrue(Query("album = /i Hate/i").search(self.s1))
        self.assertTrue(Query("title = /ångström/").search(self.s4))
        self.assertFalse(Query("album = /i hate/c").search(self.s1))
        self.assertFalse(Query("title = /ångström/c").search(self.s4))

    def test_re_and(self):
        self.assertTrue(Query("album = &(/ate/,/est/)").search(self.s1))
        self.assertFalse(Query("album = &(/ate/, /ets/)").search(self.s1))
        self.assertFalse(Query("album = &(/tate/, /ets/)").search(self.s1))

    def test_re_or(self):
        self.assertTrue(Query("album = |(/ate/,/est/)").search(self.s1))
        self.assertTrue(Query("album = |(/ate/,/ets/)").search(self.s1))
        self.assertFalse(Query("album = |(/tate/, /ets/)").search(self.s1))

    def test_newlines(self):
        self.assertTrue(Query("a = /\n/").search(self.s3))
        self.assertTrue(Query("a = /\\n/").search(self.s3))
        self.assertFalse(Query("a = /\n/").search(self.s2))
        self.assertFalse(Query("a = /\\n/").search(self.s2))

    def test_exp_and(self):
        self.assertTrue(Query("&(album = ate, artist = man)").search(self.s1))
        self.assertFalse(Query("&(album = ate, artist = nam)").search(self.s1))
        self.assertFalse(Query("&(album = tea, artist = nam)").search(self.s1))

    def test_exp_or(self):
        self.assertTrue(Query("|(album = ate, artist = man)").search(self.s1))
        self.assertTrue(Query("|(album = ate, artist = nam)").search(self.s1))
        self.assertFalse(Query("&(album = tea, artist = nam)").search(self.s1))

    def test_dumb_search(self):
        self.assertTrue(Query("ate man").search(self.s1))
        self.assertTrue(Query("Ate man").search(self.s1))
        self.assertFalse(Query("woo man").search(self.s1))
        self.assertFalse(Query("not crazy").search(self.s1))

    def test_dumb_search_value(self):
        self.assertTrue(Query("|(ate, foobar)").search(self.s1))
        self.assertTrue(Query("!!|(ate, foobar)").search(self.s1))
        self.assertTrue(Query("&(ate, te)").search(self.s1))
        self.assertFalse(Query("|(foo, bar)").search(self.s1))
        self.assertFalse(Query("&(ate, foobar)").search(self.s1))
        self.assertFalse(Query("! !&(ate, foobar)").search(self.s1))
        self.assertFalse(Query("&blah").search(self.s1))
        self.assertTrue(Query("&blah oh").search(self.s5))
        self.assertTrue(Query("!oh no").search(self.s5))
        self.assertFalse(Query("|blah").search(self.s1))
        # https://github.com/quodlibet/quodlibet/issues/1056
        self.assertTrue(Query("&(ate, piman)").search(self.s1))

    def test_dumb_search_value_negate(self):
        self.assertTrue(Query("!xyz").search(self.s1))
        self.assertTrue(Query("!!!xyz").search(self.s1))
        self.assertTrue(Query(" !!!&(xyz, zyx)").search(self.s1))
        self.assertFalse(Query("!man").search(self.s1))

        self.assertTrue(Query("&(tests,piman)").search(self.s1))
        self.assertTrue(Query("&(tests,!nope)").search(self.s1))
        self.assertFalse(Query("&(tests,!!nope)").search(self.s1))
        self.assertFalse(Query("&(tests,!piman)").search(self.s1))
        self.assertTrue(Query("&(tests,|(foo,&(pi,!nope)))").search(self.s1))

    def test_dumb_search_regexp(self):
        self.assertTrue(Query("/(x|H)ate/").search(self.s1))
        self.assertTrue(Query("'PiMan'").search(self.s1))
        self.assertFalse(Query("'PiMan'c").search(self.s1))
        self.assertTrue(Query("!'PiMan'c").search(self.s1))
        self.assertFalse(Query("!/(x|H)ate/").search(self.s1))

    def test_unslashed_search(self):
        self.assertTrue(Query("artist=piman").search(self.s1))
        self.assertTrue(Query("title=ång").search(self.s4))
        self.assertFalse(Query("artist=mu").search(self.s1))
        self.assertFalse(Query("title=äng").search(self.s4))

    def test_synth_search(self):
        self.assertTrue(Query("~dirname=/dir1/").search(self.s1))
        self.assertTrue(Query("~dirname=/dir2/").search(self.s2))
        self.assertFalse(Query("~dirname=/dirty/").search(self.s1))
        self.assertFalse(Query("~dirname=/dirty/").search(self.s2))

    def test_search_almostequal(self):
        a, b = AudioFile({"~#rating": 0.771}), AudioFile({"~#rating": 0.769})
        self.assertTrue(Query("#(rating = 0.77)").search(a))
        self.assertTrue(Query("#(rating = 0.77)").search(b))

    def test_and_or_neg_operator(self):
        union = Query("|(foo=bar,bar=foo)")
        inter = Query("&(foo=bar,bar=foo)")
        neg = Query("!foo=bar")
        numcmp = Query("#(bar = 0)")
        tag = Query("foo=bar")

        tests = [inter | tag, tag | tag, neg | neg, tag | inter, neg | union,
            union | union, inter | inter, numcmp | numcmp, numcmp | union]

        self.assertFalse([x for x in tests if not isinstance(x, match.Union)])

        tests = [inter & tag, tag & tag, neg & neg, tag & inter, neg & union,
            union & union, inter & inter, numcmp & numcmp, numcmp & inter]

        self.assertFalse([x for x in tests if not isinstance(x, match.Inter)])

        self.assertTrue(isinstance(-neg, match.Tag))

        true = Query("")
        self.assertTrue(isinstance(true | inter, match.True_))
        self.assertTrue(isinstance(inter | true, match.True_))
        self.assertTrue(isinstance(true & inter, match.Inter))
        self.assertTrue(isinstance(inter & true, match.Inter))
        self.assertTrue(isinstance(true & true, match.True_))
        self.assertTrue(isinstance(true | true, match.True_))
        self.assertTrue(isinstance(-true, match.Neg))

    def test_filter(self):
        q = Query("artist=piman")
        self.assertEqual(q.filter([self.s1, self.s2]), [self.s1])
        self.assertEqual(q.filter(iter([self.s1, self.s2])), [self.s1])

        q = Query("")
        self.assertEqual(q.filter([self.s1, self.s2]), [self.s1, self.s2])
        self.assertEqual(
            q.filter(iter([self.s1, self.s2])), [self.s1, self.s2])

    def test_match_all(self):
        self.assertTrue(Query.match_all(""))
        self.assertTrue(Query.match_all("    "))
        self.assertFalse(Query.match_all("foo"))

    def test_utf8(self):
        # also handle undecoded values
        self.assertTrue(Query("utf8=Ångström").search(self.s4))

    def test_fs_utf8(self):
        self.assertTrue(Query("~filename=foü.ogg").search(self.s3))
        self.assertTrue(Query("~filename=öä").search(self.s3))
        self.assertTrue(Query("~dirname=öäü").search(self.s3))
        self.assertTrue(Query("~basename=ü.ogg").search(self.s3))

    def test_filename_utf8_fallback(self):
        self.assertTrue(Query("filename=foü.ogg").search(self.s3))
        self.assertTrue(Query("filename=öä").search(self.s3))

    def test_star_numeric(self):
        self.assertRaises(ValueError, Query, "foobar", star=["~#mtime"])

    def test_match_diacriticals_explcit(self):
        self.assertFalse(Query('title=angstrom').search(self.s4))
        self.assertFalse(Query('title="Ångstrom"').search(self.s4))
        self.assertTrue(Query('title="Ångstrom"d').search(self.s4))
        self.assertTrue(Query('title=Ångström').search(self.s4))
        self.assertTrue(Query('title="Ångström"').search(self.s4))
        self.assertTrue(Query('title=/Ångström/').search(self.s4))
        self.assertTrue(Query('title="Ångstrom"d').search(self.s4))
        self.assertTrue(Query('title=/Angstrom/d').search(self.s4))
        self.assertTrue(Query('""d').search(self.s4))

    def test_match_diacriticals_dumb(self):
        self.assertTrue(Query('Angstrom').search(self.s4))
        self.assertTrue(Query('Ångström').search(self.s4))
        self.assertTrue(Query('Ångstrom').search(self.s4))
        self.assertFalse(Query('Ängström').search(self.s4))

    def test_match_diacriticals_invalid_or_unsupported(self):
        # these fall back to test dumb searches:
        # invalid regex
        Query('/Sigur [r-zos/d')
        # group refs unsupported for diacritic matching
        Query('/(<)?(\w+@\w+(?:\.\w+)+)(?(1)>)/d')


class TQuery_get_type(TestCase):
    def test_red(self):
        for p in ["a = /w", "|(sa#"]:
            self.assertEqual(QueryType.INVALID, Query.get_type(p))

    def test_black(self):
        for p in ["a test", "more test hooray"]:
            self.assertEqual(QueryType.TEXT, Query.get_type(p))

    def test_green(self):
        for p in ["a = /b/", "&(a = b, c = d)", "/abc/", "!x", "!&(abc, def)"]:
            self.assertEqual(QueryType.VALID, Query.get_type(p))
