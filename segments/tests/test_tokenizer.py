# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import codecs
import unittest
from segments.tokenizer import Tokenizer
from segments.tree import printMultigraphs


def _test_path(fname):
    return os.path.join(os.path.dirname(__file__), fname)


def jipa(input, gold):
    with codecs.open(_test_path(input), "r", "utf-8") as infile:
        input = infile.read()
    with codecs.open(_test_path(gold), "r", "utf-8") as goldfile:
        gold = goldfile.read()
    return(input, gold)


class TokenizerTestCase(unittest.TestCase):
    """ Tests for tokenizer.py """
    maxDiff = None # for printing large output

    def setUp(self):
        self.t = Tokenizer(_test_path('test.prf'))

    def test_printTree(self):
        self.t.tree.printTree(self.t.tree.root)
        printMultigraphs(self.t.tree.root, '', '')
        printMultigraphs(self.t.tree.root, 'abcd', '')

    def test_kabiye(self):
        t = Tokenizer()
        input, gold = jipa("Kabiye_input.txt", "Kabiye_output.txt")
        result = t.tokenize_ipa(input)
        self.assertEqual(result, gold)

    def test_portuguese(self):
        t = Tokenizer()
        input, gold = jipa("Brazilian_Portuguese_input.txt", "Brazilian_Portuguese_output.txt")
        result = t.tokenize_ipa(input)
        self.assertEqual(result, gold)

    def test_vietnamese(self):
        t = Tokenizer()
        input, gold = jipa("Vietnamese_input.txt", "Vietnamese_output.txt")
        result = t.tokenize_ipa(input)
        self.assertEqual(result, gold)

    def test_german(self):
        t = Tokenizer()
        input, gold = jipa("Zurich_German_input.txt", "Zurich_German_output.txt")
        result = t.tokenize_ipa(input)
        self.assertEqual(result, gold)

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
        result = t.graphemes("aabchonn-ih")
        self.assertEqual(result, "a a b c h o n n - i h")

        result = self.t.graphemes("aabchonn-ih")
        self.assertEqual(result, "aa b ch on n - ih")

    def test_transform1(self):
        result = self.t.transform("aabchonn-ih")
        self.assertEqual(result, "aa b ch on n - ih")

    def test_transform2(self):
        result = self.t.transform("aabchonn-ih", "ipa")
        self.assertEqual(result, "aː b tʃ õ n í")

    def test_transform3(self):
        result = self.t.transform("aabchonn-ih", "XSAMPA")
        self.assertEqual(result, "a: b tS o~ n i_H")

    def test_rules(self):
        result = self.t.rules("aabchonn-ih")
        self.assertEqual(result, "ii-ii")

    def test_transform_rules(self):
        result = self.t.transform_rules("aabchonn-ih")
        self.assertEqual(result, "b b ii - ii")

    def test_find_missing_characters(self):
        result = self.t.find_missing_characters("aa b ch on n - ih x y z")
        self.assertEqual(result, "aa b ch on n - ih ? ? ?")
