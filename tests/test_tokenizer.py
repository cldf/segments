# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import codecs

from six import StringIO
import pytest

from segments.tokenizer import Tokenizer, Profile, GRAPHEME_COL
from segments.tree import printMultigraphs


def _test_path(fname):
    return os.path.join(os.path.dirname(__file__), 'data', fname)


def _test_data(fname):
    with codecs.open(_test_path(fname), "r", "utf-8") as fp:
        return fp.read()


@pytest.fixture
def tokenizer_with_profile():
    return Tokenizer(_test_path('test.prf'))


@pytest.fixture
def tokenizer():
    return Tokenizer()


@pytest.mark.parametrize(
    "lang", ['Kabiye', 'Brazilian_Portuguese', 'Vietnamese', 'Zurich_German'])
def test_jipa(lang):
    tokenize = Tokenizer()
    assert tokenize(
        _test_data(lang + '_input.txt'), ipa=True) == _test_data(lang + '_output.txt')


def test_missing_header():
    with pytest.raises(ValueError):
        Profile({})


def test_duplicate_grapheme(mocker):
    mock_log = mocker.Mock()
    mocker.patch('segments.tokenizer.logging', mocker.Mock(getLogger=lambda n: mock_log))
    Profile({'Grapheme': 'a'}, {'Grapheme': 'a'})
    assert mock_log.warn.call_args[0][0].startswith('line 3')


def test_from_textfile():
    assert 'Grapheme\t' in '%s' % Profile.from_textfile(_test_path('Kabiye_input.txt'))


def test_errors():
    t = Tokenizer(_test_path('test.prf'), errors_replace=lambda c: '<{0}>'.format(c))
    assert t('habe') == '<i> a b <e>'

    with pytest.raises(ValueError):
        t('habe', form='xyz')

    with pytest.raises(ValueError):
        t('habe', errors='strict')

    assert t('habe', errors='ignore') == 'a b'


def test_boundaries(tokenizer_with_profile):
    assert tokenizer_with_profile('aa aa', separator=' _ ') == ' b _  b'


@pytest.mark.parametrize(
    "text,kw,result",
    [
        ('n\u0303a', dict(), 'n\u0303 a'),
        ('\xf1a', dict(), 'n\u0303 a'),
        ('n\u0303a', dict(form='NFC'), '\xf1 a'),
        ('\u02b0ello', dict(ipa=True), '\u02b0e l l o'),
        ('aa', dict(form='NFC'), 'a a')
    ]
)
def test_tokenize(tokenizer, text, kw, result):
    assert tokenizer(text, **kw) == result


def test_tokenize_with_profile(tokenizer_with_profile):
    assert tokenizer_with_profile('aa') == ' b'


def test_tokenize_with_profile_from_object():
    prf = Profile(dict(Grapheme='aa', mapping='xy'), dict(Grapheme='b', mapping='z'))
    assert Tokenizer(profile=prf)('aab', column='mapping') == 'xy z'


def test_printTree(tokenizer_with_profile):
    stream = StringIO()
    tokenizer_with_profile.op.tree.printTree(
        tokenizer_with_profile.op.tree.root, stream=stream)
    stream.seek(0)
    assert 'a* -- a*' in stream.read().split('\n')
    printMultigraphs(tokenizer_with_profile.op.tree.root, '', '')
    printMultigraphs(tokenizer_with_profile.op.tree.root, 'abcd', '')


def test_characters(tokenizer):
    assert tokenizer.characters(
        "ĉháɾã̌ctʼɛ↗ʐː| k͡p") == "c ̂ h a ́ ɾ a ̃ ̌ c t ʼ ɛ ↗ ʐ ː | # k ͡ p"


def test_grapheme_clusters(tokenizer):
    result = tokenizer.grapheme_clusters("ĉháɾã̌ctʼɛ↗ʐː| k͡p")
    assert result == "ĉ h á ɾ ã̌ c t ʼ ɛ ↗ ʐ ː | # k͡ p"


def test_graphemes(tokenizer, tokenizer_with_profile):
    assert tokenizer.graphemes("aabchonn-ih") == "a a b c h o n n - i h"
    assert tokenizer_with_profile.graphemes("aabchonn-ih") == "aa b ch on n - ih"


def test_transform_errors(tokenizer_with_profile, tokenizer):
    with pytest.raises(ValueError):
        tokenizer.transform('abc')

    with pytest.raises(ValueError):
        tokenizer_with_profile.transform("aabchonn-ih", 'xx')


@pytest.mark.parametrize(
    "text,column,result",
    [
        ("aabchonn-ih", GRAPHEME_COL, "aa b ch on n - ih"),
        ("aabchonn-ih", "IPA", "aː b tʃ õ n í"),
        ("aabchonn-ih", "XSAMPA", "a: b tS o~ n i_H"),
    ]
)
def test_transform(tokenizer_with_profile, text, column, result):
    assert tokenizer_with_profile.transform(text, column=column) == result


def test_rules(tokenizer_with_profile, tokenizer):
    assert tokenizer.rules('abc') == 'abc'
    assert tokenizer_with_profile.rules("aabchonn-ih") == "  ii-ii"
    assert Tokenizer(profile=_test_path('profile_without_rules.prf')).rules('aa') != \
        tokenizer_with_profile.rules('aa')


def test_transform_rules(tokenizer_with_profile):
    assert tokenizer_with_profile.transform_rules("aabchonn-ih") == " b b ii - ii"


def test_find_missing_characters(tokenizer_with_profile):
    result = tokenizer_with_profile.find_missing_characters("aa b ch on n - ih x y z")
    assert result == "aa b ch on n - ih \ufffd \ufffd \ufffd"

    t = Tokenizer(_test_path('test.prf'), errors_replace=lambda c: '?')
    result = t.find_missing_characters("aa b ch on n - ih x y z")
    assert result == "aa b ch on n - ih ? ? ?"
