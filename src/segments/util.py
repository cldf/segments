# coding: utf-8
from __future__ import unicode_literals
from functools import partial
import unicodedata

REPLACEMENT_MARKER = '�'
NULL = "NULL"
nfd = partial(unicodedata.normalize, 'NFD')
