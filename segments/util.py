from __future__ import print_function
import unicodedata


def normalized_string(string, add_boundaries=True, form='NFD'):
    if add_boundaries:
        string = string.replace(" ", "#")
    return unicodedata.normalize(form, string)
