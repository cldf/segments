from functools import partial
import unicodedata

import regex

REPLACEMENT_MARKER = '�'
nfd = partial(unicodedata.normalize, 'NFD')
grapheme_pattern = regex.compile(r"\X", regex.UNICODE)
