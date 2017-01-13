# coding: utf8
from __future__ import unicode_literals, print_function, division
import sys
import os
import argparse
from collections import OrderedDict, Counter

from six import PY2, text_type

from segments.tokenizer import Tokenizer
from segments import util


def _print(args, line):
    if PY2:
        line = line.encode(args.encoding)
    print(line)


def _maybe_decode(s, encoding):
    if not isinstance(s, text_type):
        return s.decode(encoding)
    return s


def tokenize(args):
    _print(args, Tokenizer()(args.args[0].decode(args.encoding)))


def profile(args, stream=sys.stdin):
    """
    Create an orthography profile for a string or text file

    segments profile <STRING>|<FILENAME>
    """
    if not args.args:
        args.args = [stream.read()]

    if os.path.exists(args.args[0]):
        input_ = util.normalized_rows(args.args[0])
    else:
        input_ = [
            util.normalized_string(
                _maybe_decode(args.args[0], args.encoding), add_boundaries=False)]

    graphemes = Counter()
    for line in input_:
        graphemes.update(Tokenizer.grapheme_pattern.findall(line))

    _print(args, 'graphemes\tfrequency\tmapping')
    for grapheme, frequency in graphemes.most_common():
        _print(args, '{0}\t{1}\t{0}'.format(grapheme, frequency))


class ParserError(Exception):
    pass


class ArgumentParser(argparse.ArgumentParser):  # pragma: no cover
    """
    An command line argument parser supporting sub-commands in a simple way.
    """
    def __init__(self, *commands, **kw):
        kw.setdefault(
            'description', "Main command line interface of the segments package.")
        kw.setdefault(
            'epilog', "Use '%(prog)s help <cmd>' to get help about individual commands.")
        argparse.ArgumentParser.__init__(self, **kw)
        self.commands = OrderedDict([(cmd.__name__, cmd) for cmd in commands])
        self.add_argument("--encoding", default="utf8")
        self.add_argument('command', help='|'.join(self.commands.keys()))
        self.add_argument('args', nargs=argparse.REMAINDER)

    def main(self, args=None, catch_all=False):
        args = self.parse_args(args=args)
        if args.command == 'help':
            # As help text for individual commands we simply re-use the docstrings of the
            # callables registered for the command:
            print(self.commands[args.args[0]].__doc__)
        else:
            if args.command not in self.commands:
                print('invalid command')
                self.print_help()
                return 64
            try:
                self.commands[args.command](args)
            except ParserError as e:
                print(e)
                print(self.commands[args.command].__doc__)
                return 64
            except Exception as e:
                if catch_all:
                    print(e)
                    return 1
                raise
        return 0


def main():  # pragma: no cover
    parser = ArgumentParser(tokenize, profile)
    sys.exit(parser.main())
