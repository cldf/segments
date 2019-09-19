"""
Default implementations for error handlers
"""
import logging

from segments.util import REPLACEMENT_MARKER

log = logging.getLogger(__name__)


def strict(c):
    log.debug('invalid grapheme: {0}'.format(c))
    raise ValueError('invalid grapheme')


def replace(c):
    log.debug('replacing grapheme: {0}'.format(c))
    return REPLACEMENT_MARKER


def ignore(c):
    log.debug('ignoring grapheme: {0}'.format(c))
    return ''
