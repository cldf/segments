# coding: utf8
from __future__ import unicode_literals
import io


def test_tokenize(capsys, mocker):
    from segments.__main__ import tokenize

    tokenize(mocker.Mock(args=['abc'.encode('utf8')], encoding='utf8', profile=None))
    out, err = capsys.readouterr()
    assert out.strip() == 'a b c'


def test_tokenize_from_stdin(capsys, mocker):
    from segments.__main__ import tokenize

    mocker.patch('segments.__main__.sys.stdin', io.StringIO('abc'))
    tokenize(mocker.Mock(args=[], encoding='utf8', profile=None))
    out, err = capsys.readouterr()
    assert out.strip() == 'a b c'


def test_profile(capsys, mocker):
    from segments.__main__ import profile

    profile(mocker.Mock(args=['abcaba'.encode('utf8')], encoding='utf8'))
    out, err = capsys.readouterr()
    assert 'a\t3\ta' in out.split('\n')
