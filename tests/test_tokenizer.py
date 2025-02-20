import unicodedata

import pytest

from segments import Tokenizer, Profile, Rules, REPLACEMENT_MARKER


def _read_data(fname):
    return fname.read_text(encoding="utf-8")


@pytest.fixture
def tokenizer_with_profile(profile_path):
    return Tokenizer(profile_path)


@pytest.fixture
def tokenizer():
    return Tokenizer()


@pytest.mark.parametrize(
    "lang", ['Kabiye', 'Brazilian_Portuguese', 'Vietnamese', 'Zurich_German'])
def test_jipa(lang, testdata):
    tokenize = Tokenizer()
    assert tokenize(_read_data(testdata / (lang + '_input.txt')), ipa=True) ==\
        _read_data(testdata / (lang + '_output.txt'))


def test_single_combining_character():
    assert Tokenizer()("ˈ", ipa=True) == "ˈ"
    assert Tokenizer()("ʲ", ipa=True) == "ʲ"


def test_characters():
    t = Tokenizer()
    assert t.characters("ĉháɾã̌ctʼɛ↗ʐː| k͡p") == "c ̂ h a ́ ɾ a ̃ ̌ c t ʼ ɛ ↗ ʐ ː | # k ͡ p"
    assert t.characters('abc def', segment_separator='_', separator='|') == 'a_b_c|d_e_f'


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
    assert t('x', column='Out') == REPLACEMENT_MARKER

    prf = Profile(
        {'Grapheme': 'uu'},
        {'Grapheme': 'b'},
        {'Grapheme': 'o'},
    )
    t = Tokenizer(profile=prf)
    assert t('uubo uubo') == 'uu b o # uu b o'


def test_normalization():
    specs = [
        {'Grapheme': 'ä'},
        {'Grapheme': 'aa'},
        {'Grapheme': 'a'},
    ]
    prf = Profile(*specs, **{'form': 'NFD'})
    t = Tokenizer(profile=prf)
    # "aa" matches, because the "ä" is decomposed:
    assert t(unicodedata.normalize('NFD', 'aä')) == 'aa ' + REPLACEMENT_MARKER
    # A composed "ä" doesn't match anymore:
    assert t(unicodedata.normalize('NFC', 'aä')) == 'a ' + REPLACEMENT_MARKER
    prf = Profile(*specs, **{'form': 'NFC'})
    t = Tokenizer(profile=prf)
    # "aa" doesn't match here, this is typically the behaviour one wants:
    assert t(unicodedata.normalize('NFC', 'aä')) == 'a ä'
    assert t(unicodedata.normalize('NFD', 'aä')) == 'aa ' + REPLACEMENT_MARKER


def test_errors(profile_path):
    t = Tokenizer(profile_path, errors_replace=lambda c: '<{0}>'.format(c))
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
        ("ʔɓaːn˧˩ ŋaː˦ˀ˥", dict(ipa=True), "ʔ ɓ aː n ˧˩ # ŋ aː ˦ˀ˥"),
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
        ("aabchonn-ih", Profile.GRAPHEME_COL, "aa b ch on n - ih"),
        ("aabchonn-ih", "IPA", "aː b tʃ õ n í"),
        ("aabchonn-ih", "XSAMPA", "a: b tS o~ n i_H"),
    ]
)
def test_transform(tokenizer_with_profile, text, column, result):
    tokenizer_with_profile._rules = None
    assert tokenizer_with_profile(text, column=column) == result


def test_rules(tokenizer_with_profile, tokenizer, testdata):
    assert tokenizer.rules('abc') == 'abc'
    assert tokenizer_with_profile.rules("aabchonn-ih") == "  ii-ii"
    assert Tokenizer(profile=testdata / 'profile_without_rules.prf').rules('aa') != \
        tokenizer_with_profile.rules('aa')
    rules = Rules((r'(a|á|e|é|i|í|o|ó|u|ú)(n)(\s)(a|á|e|é|i|í|o|ó|u|ú)', r'\1 \2 \4'))
    assert rules.apply('tan ab') == 'ta n ab'
