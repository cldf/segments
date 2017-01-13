# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase
import os
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

        with capture(tokenize, Mock(args=['abc'.encode('utf8')], encoding='utf8')) as out:
            self.assertEqual(out.strip(), 'a b c')

    def test_profile(self):
        from segments.cli import profile

        stream = StringIO('abcd')
        with capture(profile, Mock(args=[], encoding='utf8'), stream=stream) as o:
            stream.close()
            self.assertIn('a\t1\ta', o.split('\n'))

        with capture(
            profile,
            Mock(args=[os.path.join(os.path.dirname(__file__), 'test.prf')],
                 encoding='utf8')
        ) as o:
            self.assertTrue(bool(o.split('\n')))

        with capture(profile, Mock(args=['abcaba'.encode('utf8')], encoding='utf8')) as o:
            self.assertIn('a\t3\ta', o.split('\n'))
