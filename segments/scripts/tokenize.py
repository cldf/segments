#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""tokenize

Usage:
  tokenize <profile>...
  tokenize -h | --help
  tokenize --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

from __future__ import unicode_literals, print_function
from docopt import docopt

__version__ = "0.1.0"
__author__ = "Steven Moran"
__license__ = "MIT"


def main():
    """Main entry point for the tokenize CLI."""
    args = docopt(__doc__, version=__version__)
    print(args)

if __name__ == '__main__':
    main()