# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase
import sys
from contextlib import contextmanager

from six import StringIO, text_type
from mock import Mock


@contextmanager
def capture(func, *args, **kw):
    out, sys.stdout = sys.stdout, StringIO()
    func(*args, **kw)
    sys.stdout.seek(0)
    res = sys.stdout.read()
    if not isinstance(res, text_type):
        res = res.decode('utf8')  # pragma: no cover
    yield res
    sys.stdout = out


class Tests(TestCase):
    def test_tokenize(self):
        from segments.cli import tokenize

        with capture(
            tokenize,
            Mock(args=['abc'.encode('utf8')], encoding='utf8', profile=None)
        ) as out:
            self.assertEqual(out.strip(), 'a b c')

    def test_profile(self):
        from segments.cli import profile

        with capture(profile, Mock(args=['abcaba'.encode('utf8')], encoding='utf8')) as o:
            self.assertIn('a\t3\ta', o.split('\n'))
