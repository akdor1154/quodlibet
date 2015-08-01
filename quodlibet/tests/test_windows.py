# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import os
import sys

from tests import TestCase, DATA_DIR, skipUnless

from quodlibet.util.path import normalize_path
from quodlibet import windows


@skipUnless(os.name == "nt", "Wrong platform", warn=False)
class TWindows(TestCase):

    def test_dir_funcs(self):
        d = windows.get_personal_dir()
        self.assertTrue(d is None or isinstance(d, str))

        d = windows.get_appdate_dir()
        self.assertTrue(d is None or isinstance(d, str))

        d = windows.get_desktop_dir()
        self.assertTrue(d is None or isinstance(d, str))

        d = windows.get_music_dir()
        self.assertTrue(d is None or isinstance(d, str))

        d = windows.get_profile_dir()
        self.assertTrue(d is None or isinstance(d, str))

        d = windows.get_links_dir()
        self.assertTrue(d is None or isinstance(d, str))

    def test_get_link_target(self):
        path = os.path.join(DATA_DIR, "test.lnk")
        d = windows.get_link_target(path)
        self.assertEqual(
            normalize_path(d), normalize_path("C:\Windows\explorer.exe"))
        self.assertTrue(isinstance(d, str))

    def test_get_link_target_latin1(self):
        path = os.path.join(DATA_DIR, "test2.lnk")
        d = windows.get_link_target(path)
        # the second char is only not in latin-1
        self.assertEqual(os.path.basename(d), "\xe1??.txt")
        self.assertTrue(isinstance(d, str))

    def test_environ(self):
        env = windows.WindowsEnviron()
        len_ = len(env)
        env["FOO"] = "bar"
        self.assertEqual(len(env), len_ + 1)
        self.assertEqual(env.get("FOO"), "bar")
        self.assertTrue("FOO" in repr(env))
        self.assertEqual(len(list(env)), len(env))
        del env["FOO"]

    def test_environ_ascii(self):
        env = windows.WindowsEnviron()
        env["FOO"] = "bar"
        env["FOO"]
        del env["FOO"]


@skipUnless(os.name == "nt", "Wrong platform", warn=False)
class Tget_win32_unicode_argv(TestCase):

    def test_main(self):
        newargv = windows.get_win32_unicode_argv()
        self.assertEqual(len(sys.argv), len(newargv))
        if newargv:
            self.assertTrue(isinstance(newargv[0], str))
