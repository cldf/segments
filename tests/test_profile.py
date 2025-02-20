import json
from copy import deepcopy

import pytest

from segments import Profile


def test_duplicate_grapheme(mocker):
    logging = mocker.patch('segments.profile.logging')
    Profile({'Grapheme': 'a'}, {'Grapheme': 'a'})
    assert logging.getLogger.return_value.warning.call_args[0][0].startswith('line 3')


def test_missing_grapheme():
    with pytest.raises(ValueError):
        Profile({})

    with pytest.raises(ValueError):
        Profile({'Grapheme': ''})


def test_profile_with_bad_metadata(tmp_path):
    mdpath = tmp_path / 'md.json'
    md = deepcopy(Profile.MD)
    md['tables'].append({'tableSchema': {'columns': []}})
    mdpath.write_text(json.dumps(md), encoding='utf-8')

    with pytest.raises(ValueError):
        Profile.from_file(str(mdpath))


def test_Profile_from_file(profile_path):
    res = Profile.from_file(profile_path)
    assert 'aa' in res.graphemes
    assert res.graphemes['aa']['XSAMPA'] == 'a:'
    assert res.graphemes['-']['XSAMPA'] is None


def test_Profile_from_metadata(testdata):
    res = Profile.from_file(testdata / 'profile.json', form='NFD')
    assert 'ch' in res.graphemes
    assert res.graphemes['ch']['XSAMPA'] == 'tS'
    assert res.graphemes['-']['XSAMPA'] is None
    assert res.metadata['dc:language'] == 'abcd1234'


def test_from_text():
    res = Profile.from_text('abcdabcab')
    assert 'a' in res.graphemes
    assert res.graphemes['a']['frequency'] == 3


def test_from_textfile(testdata):
    res = Profile.from_textfile(testdata / 'Kabiye_input.txt')
    assert 'à̙' in res.graphemes
    assert res.graphemes['à̙']['frequency'] == 20
