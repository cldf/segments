#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create (initial) orthography profiles. Input should be UTF-8 plain text.

Usage:
  create_profiles [options] <textfile>
  create_profiles -h | --help
  create_profiles --version

Options:
  --verbose     Show processing info.
  --out=<dir>   Directory to which to write the profiles [default: .]
  -h --help     Show this screen.
  --version     Show version.
"""
from __future__ import unicode_literals, print_function
import os
import collections
import regex as re
from io import open

from docopt import docopt

from segments.util import normalized_rows

__version__ = "0.1.0"
__author__ = "Steven Moran"
__license__ = "MIT"


def main():  # pragma: no cover
    """Main entry point for the tokenize CLI."""
    args = docopt(__doc__, version=__version__)
    create_profiles(args['<textfile>'], args['--out'], verbose=args['--verbose'])


def create_profiles(filename, out, verbose=False):
    characters = collections.Counter()
    graphemes = collections.Counter()

    grapheme_pattern = re.compile("\X", re.UNICODE)
    for line in normalized_rows(filename, None):
        # remove white space?
        # line = line.replace(" ", "")
        characters.update(line)
        if verbose:
            print(characters)  # pragma: no cover
        graphs = grapheme_pattern.findall(line)
        graphemes.update(graphs)
        if verbose:
            print(graphemes)  # pragma: no cover

    for counter, name in [
        (characters, 'unicode_characters'),
        (graphemes, 'grapheme_clusters'),
    ]:
        with open(os.path.join(out, "op_%s.tsv" % name), "w", encoding='utf8') as f:
            for c, count in counter.most_common():
                f.write('%s\t%7d\n' % (c, count))


if __name__ == '__main__':  # pragma: no cover
    main()
