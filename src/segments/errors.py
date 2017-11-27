# coding: utf8
"""
Default implementations for error handlers
"""
from __future__ import unicode_literals, print_function, division
import logging

log = logging.getLogger(__name__)


def strict(c):
    log.debug('invalid grapheme: {0}'.format(c))
    raise ValueError('invalid grapheme')


def replace(c):
    log.debug('replacing grapheme: {0}'.format(c))
    return '\ufffd'


def ignore(c):
    log.debug('ignoring grapheme: {0}'.format(c))
    return ''
