from __future__ import print_function
import codecs
import unicodedata


def normalized_rows(path, delimiter=None, skip_comments=True, all_lines=False):
    """
    Normalize and yield lines from a file.

    Parameters
    ----------
    path : Filesystem path.
    delimiter : If not `None`, lines will be split using this delimiter.
    skip_comments : If `True`, comment lines will be skipped.
    all_lines : If `True`, a result will be generated for each line. Lines which would
        have been skipped will yield `None`. This allows for better error reporting,
        because accurate line numbers can be reported.

    Returns
    -------
    A generator of non-empty, non-comment, normalized lines, optionally split into cols.
    """
    for line in codecs.open(path, 'r', 'utf8'):
        line = unicodedata.normalize('NFD', line).strip()

        if not line or (skip_comments and line.startswith('#')):
            res = None
        else:
            res = [col.strip() for col in line.split(delimiter)] if delimiter else line

        if all_lines or res:
            yield res


def normalized_string(string, add_boundaries=True, form='NFD'):
    if add_boundaries:
        string = string.replace(" ", "#")
    return unicodedata.normalize(form, string)
