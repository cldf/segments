# coding: utf8
from __future__ import unicode_literals, print_function, division
import sys
from collections import Counter

from six import PY2, text_type
from clldutils.path import Path
from clldutils.clilib import ArgumentParser, command, ParserError

from segments.tokenizer import Tokenizer
from segments import util


def _print(args, line):
    if PY2:
        line = line.encode(args.encoding)
    print(line)


def _get_input(args):
    string = args.args[0] if args.args else sys.stdin.read()
    if not isinstance(string, text_type):
        string = string.decode(args.encoding)
    return util.normalized_string(string.strip(), add_boundaries=False)


@command()
def tokenize(args):
    """
    Tokenize a string (passed as argument or read from stdin)

    segments [--profile=PATH/TO/PROFILE] tokenize [STRING]
    """
    if args.profile and not Path(args.profile).exists():  # pragma: no cover
        raise ParserError('--profile must be a path for an existing file')
    _print(args, Tokenizer(profile=args.profile)(_get_input(args), column=args.mapping))


@command()
def profile(args):
    """
    Create an orthography profile for a string (passed as argument or read from stdin)

    segments profile [STRING]
    """
    graphemes = Counter(Tokenizer.grapheme_pattern.findall(_get_input(args)))
    _print(args, 'Grapheme\tfrequency\tmapping')
    for grapheme, frequency in graphemes.most_common():
        _print(args, '{0}\t{1}\t{0}'.format(grapheme, frequency))


def main():  # pragma: no cover
    parser = ArgumentParser('segments')
    parser.add_argument("--encoding", help='input encoding', default="utf8")
    parser.add_argument("--profile", help='path to an orthography profile', default=None)
    parser.add_argument(
        "--mapping", help='column name in ortho profile to map graphemes', default=None)
    sys.exit(parser.main())
