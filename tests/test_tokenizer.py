# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import io

import pytest

from segments.tokenizer import Tokenizer, Profile, GRAPHEME_COL, Rules


def _test_path(fname):
    return os.path.join(os.path.dirname(__file__), 'data', fname)


def _test_data(fname):
    with io.open(_test_path(fname), mode="r", encoding="utf-8") as fp:
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
    logging = mocker.patch('segments.tokenizer.logging')
    Profile({'Grapheme': 'a'}, {'Grapheme': 'a'})
    assert logging.getLogger.return_value.warn.call_args[0][0].startswith('line 3')


def test_profile():
    prf = Profile(
        {'Grapheme': 'bischen', 'Out': 'b i s ch e n'},
        {'Grapheme': 'sch', 'Out': 'sch'},
        {'Grapheme': 'n', 'Out': 'n'},
        {'Grapheme': 'a', 'Out': 'a'},
        {'Grapheme': 'e', 'Out': 'e'},
        {'Grapheme': 'n', 'Out': 'n'},
    )
    t = Tokenizer(profile=prf)
    assert t('bischen', column='Out') == 'b i s ch e n'
    assert t('naschen', column='Out') == 'n a sch e n'

    prf = Profile(
        {'Grapheme': 'uu'},
        {'Grapheme': 'b'},
        {'Grapheme': 'o'},
    )
    t = Tokenizer(profile=prf)
    assert t('uubo uubo') == 'uu b o # uu b o'


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
        ('aa', dict(form='NFC'), 'a a'),
        ("ĉháɾã̌ctʼɛ↗ʐː| k͡p", {}, "ĉ h á ɾ ã̌ c t ʼ ɛ ↗ ʐ ː | # k͡ p"),
        ("aabchonn-ih", {}, "a a b c h o n n - i h"),
    ]
)
def test_tokenize(tokenizer, text, kw, result):
    assert tokenizer(text, **kw) == result


def test_tokenize_with_profile(tokenizer_with_profile):
    assert tokenizer_with_profile('aa') == ' b'
    assert tokenizer_with_profile("aabchonn-ih") == " b b ii - ii"


def test_tokenize_with_profile_from_object():
    prf = Profile(
        dict(Grapheme='aa', mapping=['x', 'y']),
        dict(Grapheme='b', mapping='z'))
    assert Tokenizer(profile=prf)('aab', column='mapping') == 'x y z'


def test_transform_errors(tokenizer_with_profile, tokenizer):
    with pytest.raises(AssertionError):
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
    tokenizer_with_profile._rules = None
    assert tokenizer_with_profile(text, column=column) == result


def test_rules(tokenizer_with_profile, tokenizer):
    assert tokenizer.rules('abc') == 'abc'
    assert tokenizer_with_profile.rules("aabchonn-ih") == "  ii-ii"
    assert Tokenizer(profile=_test_path('profile_without_rules.prf')).rules('aa') != \
        tokenizer_with_profile.rules('aa')
    rules = Rules((r'(a|á|e|é|i|í|o|ó|u|ú)(n)(\s)(a|á|e|é|i|í|o|ó|u|ú)', r'\1 \2 \4'))
    assert rules.apply('tan ab') == 'ta n ab'
