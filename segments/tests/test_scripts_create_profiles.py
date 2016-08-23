# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import unittest
from tempfile import mkdtemp
from shutil import rmtree


class TestCreateProfiles(unittest.TestCase):
    def setUp(self):
        self.tmp = mkdtemp()

    def tearDown(self):
        rmtree(self.tmp, ignore_errors=True)

    def test_create_profiles(self):
        from segments.scripts.create_profiles import create_profiles

        create_profiles(os.path.join(os.path.dirname(__file__), 'test.prf'), self.tmp)
        self.assertTrue(
            os.path.exists(os.path.join(self.tmp, 'op_unicode_characters.tsv')))
