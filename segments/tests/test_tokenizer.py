# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import codecs
import unittest

from six import StringIO
from nose import tools
from mock import Mock, patch

from segments.tokenizer import Tokenizer, Profile
from segments.tree import printMultigraphs


def _test_path(fname):
    return os.path.join(os.path.dirname(__file__), fname)


def test_jipa():
    def check(lang):
        tokenize = Tokenizer()
        with codecs.open(_test_path(lang + '_input.txt'), "r", "utf-8") as infile:
            input = infile.read()
        with codecs.open(_test_path(lang + '_output.txt'), "r", "utf-8") as goldfile:
            gold = goldfile.read()
        tools.assert_equal(tokenize(input, ipa=True), gold)

    for lang in ['Kabiye', 'Brazilian_Portuguese', 'Vietnamese', 'Zurich_German']:
        yield check, lang


class TestProfile(unittest.TestCase):
    def test_missing_header(self):
        with self.assertRaises(ValueError):
            Profile([['a', 'b'], ['a', 'b']])

    def test_duplicate_grapheme(self):
        mock_log = Mock()
        with patch('segments.tokenizer.logging', Mock(getLogger=lambda n: mock_log)):
            Profile([['graphemes', 'other'], ['a', 'b'], ['a', 'b']])
            assert mock_log.warn.call_args[0][0].startswith('line 3')


class TokenizerTestCase(unittest.TestCase):
    """ Tests for tokenizer.py """
    maxDiff = None  # for printing large output

    def setUp(self):
        self.t = Tokenizer(_test_path('test.prf'))

    def test_errors(self):
        t = Tokenizer(_test_path('test.prf'), errors_replace=lambda c: '<{0}>'.format(c))
        self.assertEqual(t('habe'), '<i> a b <e>')

        with self.assertRaises(ValueError):
            t('habe', form='xyz')

        with self.assertRaises(ValueError):
            t('habe', errors='strict')

        self.assertEqual(t('habe', errors='ignore'), 'a b')

    def test_boundaries(self):
        self.assertEqual(self.t('aa aa', separator=' _ '), 'b _ b')

    def test_normalization(self):
        t = Tokenizer()
        s = 'n\u0303a'
        self.assertEqual(t(s), 'n\u0303 a')
        self.assertEqual(t('\xf1a'), 'n\u0303 a')
        self.assertEqual(t(s, form='NFC'), '\xf1 a')

    def test_ipa(self):
        t = Tokenizer()
        self.assertEqual(t('\u02b0ello', ipa=True), '\u02b0e l l o')

    def test_tokenize_with_profile(self):
        self.assertEqual(self.t('aa'), 'b')

    def test_tokenize_without_profile(self):
        self.assertEqual(Tokenizer()('aa', form='NFC'), 'a a')

    def test_printTree(self):
        stream = StringIO()
        self.t.op.tree.printTree(self.t.op.tree.root, stream=stream)
        stream.seek(0)
        self.assertIn('a* -- a*', stream.read().split('\n'))
        printMultigraphs(self.t.op.tree.root, '', '')
        printMultigraphs(self.t.op.tree.root, 'abcd', '')

    def test_characters(self):
        t = Tokenizer()
        result = t.characters("ĉháɾã̌ctʼɛ↗ʐː| k͡p")
        self.assertEqual(result, "c ̂ h a ́ ɾ a ̃ ̌ c t ʼ ɛ ↗ ʐ ː | # k ͡ p")

    def test_grapheme_clusters(self):
        t = Tokenizer()
        result = t.grapheme_clusters("ĉháɾã̌ctʼɛ↗ʐː| k͡p")
        self.assertEqual(result, "ĉ h á ɾ ã̌ c t ʼ ɛ ↗ ʐ ː | # k͡ p")

    def test_graphemes(self):
        t = Tokenizer()
        self.assertEqual(t.graphemes("aabchonn-ih"), "a a b c h o n n - i h")
        self.assertEqual(self.t.graphemes("aabchonn-ih"), "aa b ch on n - ih")

    def test_transform1(self):
        self.assertEqual(self.t.transform("aabchonn-ih"), "aa b ch on n - ih")

        with self.assertRaises(ValueError):
            Tokenizer().transform('abc')

        with self.assertRaises(ValueError):
            self.assertEqual(self.t.transform("aabchonn-ih", 'xx'), "aa b ch on n - ih")

    def test_transform2(self):
        result = self.t.transform("aabchonn-ih", "ipa")
        self.assertEqual(result, "aː b tʃ õ n í")

    def test_transform3(self):
        result = self.t.transform("aabchonn-ih", "XSAMPA")
        self.assertEqual(result, "a: b tS o~ n i_H")

    def test_rules(self):
        self.assertEqual(Tokenizer().rules('abc'), 'abc')
        result = self.t.rules("aabchonn-ih")
        self.assertEqual(result, "ii-ii")

    def test_transform_rules(self):
        result = self.t.transform_rules("aabchonn-ih")
        self.assertEqual(result, "b b ii - ii")

    def test_find_missing_characters(self):
        result = self.t.find_missing_characters("aa b ch on n - ih x y z")
        self.assertEqual(result, "aa b ch on n - ih \ufffd \ufffd \ufffd")

        t = Tokenizer(_test_path('test.prf'), errors_replace=lambda c: '?')
        result = t.find_missing_characters("aa b ch on n - ih x y z")
        self.assertEqual(result, "aa b ch on n - ih ? ? ?")
