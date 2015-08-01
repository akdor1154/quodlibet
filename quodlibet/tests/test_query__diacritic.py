# -*- coding: utf-8 -*-
# Copyright 2014 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import re

from tests import TestCase

from quodlibet.query._diacritic import re_add_variants, \
    diacritic_for_letters, re_replace_literals


class TDiacritics(TestCase):

    def test_mapping(self):
        cache = diacritic_for_letters(False)
        new = diacritic_for_letters(True)
        self.assertEqual(sorted(cache.items()), sorted(new.items()))

    def test_re_replace(self):
        r = re_add_variants("aa")
        self.assertTrue("[" in r and "]" in r and r.count("ä") == 2)

    def test_re_replace_escape(self):
        r = re_add_variants("n\\n")
        self.assertEqual(r, "[nñńņňǹṅṇṉṋ]\n")

    def test_construct_regexp(self):
        res = [
            ("^a\aa[ha-z]k{1,3}h*h+h?(x|yy)(a+b|cd)$", None),
            ("(?=Asimov)", None),
            ("(?!Asimov)", None),
            ("(?<=abc)def", None),
            ("(?<!foo)", None),
            ("(?:foo)", None),
            ("(?#foo)", ""),
            ("(.+) \1", None),
            ("\\A\\b\\B\\d\\D\\s\\S\\w\\W\\Z\a",
             "\\A\\b\\B[\\d][\\D][\\s][\\S][\\w][\\W]\\Z\a"),
            ("a{3,5}?a+?a*?a??", None),
            ("^foo$", None),
            ("[-+]?(\\d+(\\.\\d*)?|\\.\\d+)([eE][-+]?\\d+)?",
             "[\\-\\+]?([\\d]+(\\.[\\d]*)?|\\.[\\d]+)([eE][\\-\\+]?[\\d]+)?"),
            ("(\$\d*)", "(\\$[\\d]*)"),
            ("\\$\\.\\^\\[\\]\\:\\-\\+\\?\\\\", None),
            ("[^a][^ab]", None),
            ("[ab][abc]", None),
        ]

        for r, o in res:
            if o is None:
                o = r
            self.assertEqual(re_replace_literals(r, {}), o)

    def test_construct_regexp_broken(self):
        self.assertRaises(re.error, re_replace_literals, "[", {})
        self.assertRaises(NotImplementedError,
                          re_replace_literals,
                          "(?P<quote>['\"]).*?(?P=quote)", {})

    def test_seq(self):
        self.assertEqual(re_add_variants("[x-y]"), "[ẋẍýÿŷȳẏẙỳỵỷỹx-y]")
        self.assertEqual(re_add_variants("[f-gm]"), "[ḟꝼĝğġģǧǵḡᵹf-gmḿṁṃ]")

    def test_literal(self):
        self.assertEqual(re_add_variants("f"), "[fḟꝼ]")
        self.assertTrue("ø" in re_add_variants("o"))
        self.assertTrue("Ø" in re_add_variants("O"))
        self.assertEqual(re_add_variants("[^f]"), "[^fḟꝼ]")
