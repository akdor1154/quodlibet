# -*- coding: utf-8 -*-
# Copyright 2007 Javier Kohen
#     2010, 2014 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

from tests import TestCase

from quodlibet.util import title
from quodlibet.util.string.titlecase import human_title as ht


class Ttitle(TestCase):

    def test_basics(s):
        s.assertEqual("Mama's Boy", title("mama's boy"))
        s.assertEqual("The A-Sides", title("the a-sides"))
        s.assertEqual("Hello Goodbye", title("hello goodbye"))
        s.assertEqual("HELLO GOODBYE", title("HELLO GOODBYE"))
        s.assertEqual("", title(""))

    def test_extra_spaces(s):
        s.assertEqual("  Space", title("  space"))
        s.assertEqual(" Dodgy  Spaces ", title(" dodgy  spaces "))

    def test_quirks(s):
        # This character is not an apostrophe, it's a single quote!
        s.assertEqual("Mama’S Boy", title("mama’s boy"))
        # This is actually an accent character, not an apostrophe either.
        s.assertEqual("Mama`S Boy", title("mama`s boy"))

    def test_quotes(s):
        s.assertEqual("Hello Goodbye (A Song)",
                 title("hello goodbye (a song)"))
        s.assertEqual("Hello Goodbye 'A Song'",
                 title("hello goodbye 'a song'"))
        s.assertEqual('Hello Goodbye "A Song"',
                 title('hello goodbye "a song"'))
        s.assertEqual("Hello Goodbye „A Song”",
                 title("hello goodbye „a song”"))
        s.assertEqual("Hello Goodbye ‘A Song’",
                 title("hello goodbye ‘a song’"))
        s.assertEqual("Hello Goodbye “A Song”",
                 title("hello goodbye “a song”"))
        s.assertEqual("Hello Goodbye »A Song«",
                 title("hello goodbye »a song«"))
        s.assertEqual("Hello Goodbye «A Song»",
                 title("hello goodbye «a song»"))
        s.assertEqual("\"24\" Theme",
                 title("\"24\" theme"))
        s.assertEqual("\"Mad-Dog\" Mike",
                 title("\"mad-dog\" mike"))

    def test_unicode(s):
        s.assertEqual("Fooäbar",
                 title("fooäbar"))
        s.assertEqual("Los Años Felices",
                 title("los años felices"))
        s.assertEqual("Ñandú",
                 title("ñandú"))
        s.assertEqual("Österreich",
                 title("österreich"))
        # Not a real word - there is none with this character at the beginning
        # but still Python doesn't capitalize the es-zed properly.
        # s.assertEquals(u"SSbahn", title(u"ßbahn"))

    # Old tests, somewhat redundant with the above, but you can never have
    # too many tests...

    def test_empty(self):
        self.assertEqual(title(""), "")

    def test_oneword(self):
        self.assertEqual(title("foobar"), "Foobar")

    def test_twowords(self):
        self.assertEqual(title("foo bar"), "Foo Bar")

    def test_preserve(self):
        self.assertEqual(title("fooBar"), "FooBar")

    def test_nonalphabet(self):
        self.assertEqual(title("foo 1bar"), "Foo 1bar")

    def test_two_words_and_one_not(self):
        self.assertEqual(title("foo 1  bar"), "Foo 1  Bar")

    def test_apostrophe(self):
        self.assertEqual(title("it's"), "It's")

    def test_english_human_title_case(s):
        s.assertEqual("System of a Down", ht("System Of A Down"))
        s.assertEqual("The Man with the Golden Gun",
                       ht("The Man With The Golden gun"))
        s.assertEqual("Live and Let Die", ht("Live And Let Die"))
        # Updated to match modifications to is/are/am rules:
        s.assertEqual("The Vitamins Are in My Fresh California Raisins",
                       ht("the vitamins are in my fresh california raisins"))
        s.assertEqual("Dig In",
                       ht("dig in"))
        s.assertEqual("In da Club",
                       ht("in da club"))
        # See Issue 616
        s.assertEqual(" Dodgy Are  the Spaces ",
                       ht(" dodgy are  the spaces "))
        s.assertEqual("Space:  The Final Frontier",
                       ht("Space:  the final frontier"))
        s.assertEqual("- Out of Space", ht("- out Of space"))

    def test_tricky_apostrophes(s):
        s.assertEqual("Guns 'n' Roses", ht("Guns 'n' roses"))
        s.assertEqual("Scarlett O'Hara", ht("scarlett o'hara"))
        s.assertEqual("Scarlett O'Hara", ht("Scarlett O'hara"))
        s.assertEqual("No Life 'til Leather", ht("no life 'til leather"))

    def test_english_humanise_sentences(s):
        """Checks trickier human title casing"""
        s.assertEqual("Buffy the Vampire Slayer: The Album",
                       ht("Buffy the vampire slayer: the album"))
        s.assertEqual("Killing Is My Business... and Business Is Good!",
                       ht("Killing is my business... And business is good!"))
        s.assertEqual("Herbie Hancock - The Definitive",
                       ht("herbie hancock - the definitive"))
