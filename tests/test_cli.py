import io
import argparse

import pytest

from segments.__main__ import tokenize, profile, main


def test_main(capsys):
    with pytest.raises(SystemExit):
        main(argparse.Namespace(command=None))
    out, err = capsys.readouterr()
    assert 'segments' in out

    with pytest.raises(SystemExit):
        main(argparse.Namespace(command='help', args=['tokenize']))
    out, err = capsys.readouterr()
    assert 'Tokenize' in out

    with pytest.raises(SystemExit):
        main(argparse.Namespace(command='tokenize', args=['abc'], profile=None, mapping=None))
    out, err = capsys.readouterr()
    assert 'a b c' in out

    with pytest.raises(SystemExit):
        main(argparse.Namespace(command='tokenize', args=['abc'], profile='xyz', mapping=None))
    out, err = capsys.readouterr()
    assert 'existing' in out


def test_tokenize(capsys, mocker):
    tokenize(mocker.Mock(args=['abc'.encode('utf8')], encoding='utf8', profile=None))
    out, err = capsys.readouterr()
    assert out.strip() == 'a b c'


def test_tokenize_from_stdin(capsys, mocker):
    mocker.patch('segments.__main__.sys.stdin', io.StringIO('abc'))
    tokenize(mocker.Mock(args=[], encoding='utf8', profile=None))
    out, err = capsys.readouterr()
    assert out.strip() == 'a b c'


def test_profile(capsys, mocker):
    profile(mocker.Mock(args=['abcaba'.encode('utf8')], encoding='utf8'))
    out, err = capsys.readouterr()
    profile_lines = [set(line.split('\t')) for line in out.split('\r\n')]
    assert {'a', '3', 'a'} in profile_lines
    assert {'Grapheme', 'frequency', 'mapping'} in profile_lines
