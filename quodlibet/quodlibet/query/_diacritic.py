# -*- coding: utf-8 -*-
# Copyright 2014 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

# A simple top-down parser for the query grammar. It's basically textbook,
# but it could use some cleaning up. It builds the requisite match.*
# objects as it goes, which is where the interesting stuff will happen.

"""
Ways to let ASCII characters match other unicode characters which
can be decomposed into one ASCII character and one or more combining
diacritic marks. This allows to match e.g. "Múm" using "Mum".

re_add_variants(u"Mum") =>
    u"[MḾṀṂ][uùúûüũūŭůűųưǔǖǘǚǜȕȗṳṵṷṹṻụủứừửữự][mḿṁṃ]"

This is also called Asymmetric Search:
    http://unicode.org/reports/tr10/#Asymmetric_Search

TODO: support replacing multiple characters, so AE matches Æ
"""

import sre_parse
import unicodedata
import sys

from quodlibet.util import re_escape


_DIACRITIC_CACHE = {
    '\u0300': ('AEINOUWYaeinouwy\u0391\u0395\u0397\u0399\u039f\u03a5\u03a9'
                '\u03b1\u03b5\u03b7\u03b9\u03bf\u03c5\u03c9\u0415\u0418'
                '\u0435\u0438'),
    '\u0300\u0345': '\u03b1\u03b7\u03c9',
    '\u0301': ('ACEGIKLMNOPRSUWYZacegiklmnoprsuwyz\xc6\xd8\xe6\xf8\u0391'
                '\u0395\u0397\u0399\u039f\u03a5\u03a9\u03b1\u03b5\u03b7'
                '\u03b9\u03bf\u03c5\u03c9\u0413\u041a\u0433\u043a'),
    '\u0301\u0307': 'Ss',
    '\u0301\u0345': '\u03b1\u03b7\u03c9',
    '\u0302': 'ACEGHIJOSUWYZaceghijosuwyz',
    '\u0302\u0300': 'AEOaeo',
    '\u0302\u0301': 'AEOaeo',
    '\u0302\u0303': 'AEOaeo',
    '\u0302\u0309': 'AEOaeo',
    '\u0303': 'AEINOUVYaeinouvy',
    '\u0303\u0301': 'OUou',
    '\u0303\u0304': 'Oo',
    '\u0303\u0308': 'Oo',
    '\u0304': ('AEGIOUYaegiouy\xc6\xe6\u0391\u0399\u03a5\u03b1\u03b9'
                '\u03c5\u0418\u0423\u0438\u0443'),
    '\u0304\u0300': 'EOeo',
    '\u0304\u0301': 'EOeo',
    '\u0304\u0308': 'Uu',
    '\u0306': ('AEGIOUaegiou\u0391\u0399\u03a5\u03b1\u03b9\u03c5\u0410'
                '\u0415\u0416\u0418\u0423\u0430\u0435\u0436\u0438\u0443'),
    '\u0306\u0300': 'Aa',
    '\u0306\u0301': 'Aa',
    '\u0306\u0303': 'Aa',
    '\u0306\u0309': 'Aa',
    '\u0307': 'ABCDEFGHIMNOPRSTWXYZabcdefghmnoprstwxyz',
    '\u0307\u0304': 'AOao',
    '\u0308': ('AEHIOUWXYaehiotuwxy\u0399\u03a5\u03b9\u03c5\u0406\u0410'
                '\u0415\u0416\u0417\u0418\u041e\u0423\u0427\u042b\u042d'
                '\u0430\u0435\u0436\u0437\u0438\u043e\u0443\u0447\u044b'
                '\u044d\u0456\u04d8\u04d9\u04e8\u04e9'),
    '\u0308\u0300': 'Uu\u03b9\u03c5',
    '\u0308\u0301': 'IUiu\u03b9\u03c5',
    '\u0308\u0304': 'AOUaou',
    '\u0308\u030c': 'Uu',
    '\u0308\u0342': '\u03b9\u03c5',
    '\u0309': 'AEIOUYaeiouy',
    '\u030a': 'AUauwy',
    '\u030a\u0301': 'Aa',
    '\u030b': 'OUou\u0423\u0443',
    '\u030c': 'ACDEGHIKLNORSTUZacdeghijklnorstuz\u01b7\u0292',
    '\u030c\u0307': 'Ss',
    '\u030f': 'AEIORUaeioru\u0474\u0475',
    '\u0311': 'AEIORUaeioru',
    '\u0313': ('\u0391\u0395\u0397\u0399\u039f\u03a9\u03b1\u03b5\u03b7'
                '\u03b9\u03bf\u03c1\u03c5\u03c9'),
    '\u0313\u0300': ('\u0391\u0395\u0397\u0399\u039f\u03a9\u03b1\u03b5'
                      '\u03b7\u03b9\u03bf\u03c5\u03c9'),
    '\u0313\u0300\u0345': '\u0391\u0397\u03a9\u03b1\u03b7\u03c9',
    '\u0313\u0301': ('\u0391\u0395\u0397\u0399\u039f\u03a9\u03b1\u03b5'
                      '\u03b7\u03b9\u03bf\u03c5\u03c9'),
    '\u0313\u0301\u0345': '\u0391\u0397\u03a9\u03b1\u03b7\u03c9',
    '\u0313\u0342': '\u0391\u0397\u0399\u03a9\u03b1\u03b7\u03b9\u03c5\u03c9',
    '\u0313\u0342\u0345': '\u0391\u0397\u03a9\u03b1\u03b7\u03c9',
    '\u0313\u0345': '\u0391\u0397\u03a9\u03b1\u03b7\u03c9',
    '\u0314': ('\u0391\u0395\u0397\u0399\u039f\u03a1\u03a5\u03a9\u03b1'
                '\u03b5\u03b7\u03b9\u03bf\u03c1\u03c5\u03c9'),
    '\u0314\u0300': ('\u0391\u0395\u0397\u0399\u039f\u03a5\u03a9\u03b1'
                      '\u03b5\u03b7\u03b9\u03bf\u03c5\u03c9'),
    '\u0314\u0300\u0345': '\u0391\u0397\u03a9\u03b1\u03b7\u03c9',
    '\u0314\u0301': ('\u0391\u0395\u0397\u0399\u039f\u03a5\u03a9\u03b1'
                      '\u03b5\u03b7\u03b9\u03bf\u03c5\u03c9'),
    '\u0314\u0301\u0345': '\u0391\u0397\u03a9\u03b1\u03b7\u03c9',
    '\u0314\u0342': ('\u0391\u0397\u0399\u03a5\u03a9\u03b1\u03b7\u03b9'
                      '\u03c5\u03c9'),
    '\u0314\u0342\u0345': '\u0391\u0397\u03a9\u03b1\u03b7\u03c9',
    '\u0314\u0345': '\u0391\u0397\u03a9\u03b1\u03b7\u03c9',
    '\u031b': 'OUou',
    '\u031b\u0300': 'OUou',
    '\u031b\u0301': 'OUou',
    '\u031b\u0303': 'OUou',
    '\u031b\u0309': 'OUou',
    '\u031b\u0323': 'OUou',
    '\u0323': 'ABDEHIKLMNORSTUVWYZabdehiklmnorstuvwyz',
    '\u0323\u0302': 'AEOaeo',
    '\u0323\u0304': 'LRlr',
    '\u0323\u0306': 'Aa',
    '\u0323\u0307': 'Ss',
    '\u0324': 'Uu',
    '\u0325': 'Aa',
    '\u0326': 'STst',
    '\u0327': 'CDEGHKLNRSTcdeghklnrst',
    '\u0327\u0301': 'Cc',
    '\u0327\u0306': 'Ee',
    '\u0328': 'AEIOUaeiou',
    '\u0328\u0304': 'Oo',
    '\u032d': 'DELNTUdelntu',
    '\u032e': 'Hh',
    '\u0330': 'EIUeiu',
    '\u0331': 'BDKLNRTZbdhklnrtz',
    '\u0342': '\u03b1\u03b7\u03b9\u03c5\u03c9',
    '\u0342\u0345': '\u03b1\u03b7\u03c9',
    '\u0345': '\u0391\u0397\u03a9\u03b1\u03b7\u03c9'
}

# See misc/uca_decomps.py
_UCA_DECOMPS = {
    'D': '\xd0\u0110\ua779',
    'F': '\ua77b',
    'G': '\ua77d',
    'H': '\u0126',
    'L': '\u0141',
    'O': '\xd8\u01fe',
    'R': '\ua782',
    'S': '\ua784',
    'T': '\ua786',
    'd': '\xf0\u0111\ua77a',
    'f': '\ua77c',
    'g': '\u1d79',
    'h': '\u0127\u210f',
    'l': '\u0142',
    'o': '\xf8\u01ff',
    'r': '\ua783',
    's': '\ua785',
    't': '\ua787',
    '\u03c3': ('\u03c2\u03f2\U0001d6d3\U0001d70d\U0001d747'
                '\U0001d781\U0001d7bb'),
    '\u0413': '\u0490',
    '\u041e': '\ua668\ua66a\ua66c',
    '\u0433': '\u0491',
    '\u043e': '\ua669\ua66b\ua66d',
}


def diacritic_for_letters(regenerate=False):
    """Returns a mapping for combining diacritic mark to ascii characters
    for which they can be used to combine to a single unicode char.

    (actually not ascii, but unicode from the Lu/Ll/Lt categories,
    but mainly ascii)

    Since this is quite expensive to compute, the result is a cached version
    unless regenerate != True. regenerate = True is used for unittests
    to validate the cache.
    """

    if not regenerate:
        return _DIACRITIC_CACHE

    d = {}
    for i in range(sys.maxunicode):
        u = chr(i)
        n = unicodedata.normalize("NFKD", u)
        if len(n) <= 1:
            continue
        if unicodedata.category(u) not in ("Lu", "Ll", "Lt"):
            continue
        if not all(map(unicodedata.combining, n[1:])):
            continue
        d.setdefault(n[1:], set()).add(n[0])

    for k, v in list(d.items()):
        d[k] = "".join(sorted(v))

    return d


def generate_re_mapping(_diacritic_for_letters):
    letter_to_variants = {}

    # combine combining characters with the ascii chars
    for dia, letters in _diacritic_for_letters.items():
        for c in letters:
            unichar = unicodedata.normalize("NFKC", c + dia)
            letter_to_variants.setdefault(c, []).append(unichar)

    # create strings to replace ascii with
    for k, v in list(letter_to_variants.items()):
        letter_to_variants[k] = "".join(sorted(v))

    return letter_to_variants


def _fixup_literal(literal, in_seq, mapping):
    u = chr(literal)
    if u in mapping:
        u = u + mapping[u]
    need_seq = len(u) > 1
    u = re_escape(u)
    if need_seq and not in_seq:
        u = "[%s]" % u
    return u


def _fixup_not_literal(literal, mapping):
    u = chr(literal)
    if u in mapping:
        u = u + mapping[u]
    u = re_escape(u)
    return "[^%s]" % u


def _fixup_range(start, end, mapping):
    extra = []
    for i in range(start, end + 1):
        u = chr(i)
        if u in mapping:
            extra.append(re_escape(mapping[u]))
    start = re_escape(chr(start))
    end = re_escape(chr(end))
    return "%s%s-%s" % ("".join(extra), start, end)


def _construct_regexp(pattern, mapping):
    """Raises NotImplementedError"""

    parts = []

    for op, av in pattern:
        if op == "not_literal":
            parts.append(_fixup_not_literal(av, mapping))
        elif op == "literal":
            parts.append(_fixup_literal(av, False, mapping))
        elif op == "category":
            cats = {
                "category_word": "\\w",
                "category_not_word": "\\W",
                "category_digit": "\\d",
                "category_not_digit": "\\D",
                "category_space": "\\s",
                "category_not_space": "\\S",
            }
            try:
                parts.append(cats[av])
            except KeyError:
                raise NotImplementedError(av)
        elif op == "any":
            parts.append(".")
        elif op == "negate":
            parts.append("^")
        elif op == "in":
            in_parts = []
            for entry in av:
                op, eav = entry
                if op == "literal":
                    in_parts.append(_fixup_literal(eav, True, mapping))
                else:
                    in_parts.append(_construct_regexp([entry], mapping))
            parts.append("[%s]" % ("".join(in_parts)))
        elif op == "range":
            start, end = av
            parts.append(_fixup_range(start, end, mapping))
        elif op == "max_repeat" or op == "min_repeat":
            min_, max_, pad = av
            pad = _construct_regexp(pad, mapping)
            if min_ == 1 and max_ == sre_parse.MAXREPEAT:
                parts.append("%s+" % pad)
            elif min_ == 0 and max_ == sre_parse.MAXREPEAT:
                parts.append("%s*" % pad)
            elif min_ == 0 and max_ == 1:
                parts.append("%s?" % pad)
            else:
                parts.append("%s{%d,%d}" % (pad, min_, max_))
            if op == "min_repeat":
                parts[-1] = parts[-1] + "?"
        elif op == "at":
            ats = {
                "at_beginning": "^",
                "at_end": "$",
                "at_beginning_string": "\\A",
                "at_boundary": "\\b",
                "at_non_boundary": "\\B",
                "at_end_string": "\\Z",
            }
            try:
                parts.append(ats[av])
            except KeyError:
                raise NotImplementedError(av)
        elif op == "subpattern":
            group, pad = av
            pad = _construct_regexp(pad, mapping)
            if group is None:
                parts.append("(?:%s)" % pad)
            else:
                parts.append("(%s)" % pad)
        elif op == "assert":
            direction, pad = av
            pad = _construct_regexp(pad, mapping)
            if direction == 1:
                parts.append("(?=%s)" % pad)
            elif direction == -1:
                parts.append("(?<=%s)" % pad)
            else:
                raise NotImplementedError(direction)
        elif op == "assert_not":
            direction, pad = av
            pad = _construct_regexp(pad, mapping)
            if direction == 1:
                parts.append("(?!%s)" % pad)
            elif direction == -1:
                parts.append("(?<!%s)" % pad)
            else:
                raise NotImplementedError(direction)
        elif op == "branch":
            dummy, branches = av
            branches = [_construct_regexp(b, mapping) for b in branches]
            parts.append("%s" % ("|".join(branches)))
        else:
            raise NotImplementedError(op)

    return "".join(parts)


def re_replace_literals(text, mapping):
    """Raises NotImplementedError or re.error"""

    assert isinstance(text, str)

    pattern = sre_parse.parse(text)
    return _construct_regexp(pattern, mapping)


# use _DIACRITIC_CACHE and create a lookup table
_mapping = generate_re_mapping(diacritic_for_letters(regenerate=False))

# add more from the UCA decomp dataset
for cp, repl in _UCA_DECOMPS.items():
    _mapping[cp] = _mapping.get(cp, "") + repl


def re_add_variants(text):
    """Will replace all occurrences of ascii chars
    by a bracket expression containing the character and all its
    variants with a diacritic mark.

    "föhn" -> "[fḟ]ö[hĥȟḣḥḧḩḫẖ][nñńņňǹṅṇṉṋ]"

    In case the passed in regex is invalid raises re.error.

    Supports all regexp except ones with group references. In
    case something is not supported NotImplementedError gets raised.
    """

    assert isinstance(text, str)

    return re_replace_literals(text, _mapping)
