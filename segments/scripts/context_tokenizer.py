#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tokenize texts using orthography profiles.

Usage:
  context_tokenizer create-profile [-s] [-n NORM] <profile> <wordlistfile>
  context_tokenizer tokenize [-scil] [-t COLNAME] [-p TYPE] [-m MISSING] [-o ORDER]
                    [-n NORM] <profile> <wordlistfile>
  context_tokenizer -h | --help
  context_tokenizer --version

Options:
  -s, --simple   use (or create) a simple profile without context or regex
  -c, --context  use context when matching profile rules
  -i, --ignore-case
                ignore case when matching rules
  -t COLNAME, --transliterate=COLNAME
                add transliterated words to output using column COLNAME
  -p TYPE, --parsing=TYPE
                either 'global' or 'linear' [default: global]
  -o ORDER, --order=ORDER
                comma seperated list of 'size', 'context', 'reverse'
  -m MISSING, --missing=MISSING
                character to mark positions which couldn't be tokenized
                [default: \u2047]
  -n NORM, --normalize=NORM
                normalize according to 'NFC', 'NFD', 'NFKC' or 'NFKD'
  -l, --log-rules
                log used rules for tokenisation (not together with -s)
  -h --help     Show this screen.
  -v, --version     Show version.
"""

from __future__ import unicode_literals, print_function
import sys
import os
import os.path
import io
from docopt import docopt
from segments import context_tokenizer
import unicodedata

__version__ = "0.1.0"
# flake8: noqa


def main():  # pragma: no cover
    """Main entry point for the tokenize CLI."""
    args = docopt(__doc__, version=__version__)
    if args['create-profile']:
        create_profile(args)
    elif args['tokenize']:
        tokenize(args)
    return 0

def create_profile(args):
    context_tokenizer.Profile.create_profile(args['<wordlistfile>'], args['<profile>'], args['--normalize'],
                                             args['--simple'])

def tokenize(args):
    #prepare profile
    profile = context_tokenizer.Profile.read_profile(args['<profile>'])
    if 'graphemes' not in profile.fieldnames:
        print('Error: Expecting a column named "graphemes" in the profile definition.', file=sys.stderr)
        print('\tRecognized names are "graphemes", "left", "right", "class".', file=sys.stderr)
        sys.exit(1)

    if args['--order'] is not None:
        order_spec = args['--order'].split(',')
        for spec in order_spec:
            if spec not in ('size', 'context', 'reverse'):
                print("Error: Unrecognized order criterium: '%s'" % spec, file=sys.stderr)
                sys.exit(1)
        if order_spec:
            profile.sort(order_spec)

    normalize = args['--normalize']
    if normalize:
        normalize = normalize.upper()
        if normalize not in ('NFC', 'NFD', 'NFKC', 'NFKD'):
            print("Error: Unrecognized unicode normalform: '%s'" % normalize, file=sys.stderr)
            sys.exit(1)
        profile.normalize(normalize)

    transliterate = args['--transliterate']
    if transliterate:
        transliterate = transliterate.split(',')
        for name in transliterate:
            if name not in profile.fieldnames:
                print("Error: Column '%s' for transliteration doesn't exist in profile" % name, file=sys.stderr)
                sys.exit(1)

    if args['--parsing'].lower() not in ('global', 'linear'):
        print("Error: Unknown parsing method '%s'" % args['--parsing'], file=sys.stderr)
        sys.exit(1)

    #prefix to use for filenames
    root, _ = os.path.splitext(args['<wordlistfile>'])

    #prepare wordlist
    comment_sign = '#'
    with io.open(args['<wordlistfile>']) as wordlist:
        if normalize is None:
            line_iter = (line.rstrip() for line in wordlist if not line.startswith(comment_sign))
        else:
            line_iter = context_tokenizer.iter_normalized(wordlist, normalize, comment_sign)
        #tokenize
        if args['--simple']:
            if args['--parsing'] == 'global':
                f_tokenize = context_tokenizer.tokenize_global_simple
            else:
                f_tokenize = context_tokenizer.tokenize_linear_simple
            tokenized, problem_chars = f_tokenize(line_iter, profile, transliterate, args['--ignore-case'],
                                                  args['--missing'])
        else:
            match_logger = None
            if args['--log-rules']:
                match_logger = io.open(root + '_rule_use.txt', 'w', encoding='utf8')
            if args['--parsing'] == 'global':
                f_tokenize = context_tokenizer.tokenize_global
            else:
                f_tokenize = context_tokenizer.tokenize_linear
            tokenized, problem_chars = f_tokenize(line_iter, profile, transliterate, args['--context'],
                                                  args['--ignore-case'], args['--missing'], match_logger)

    #write out results
    #profile
    filename = root + '_profile.tsv'
    with io.open(filename, 'w', encoding='utf8') as fp:
        profile.save(fp)

    #problematic characters
    filename = root + '_missing_chars.tsv'
    with io.open(filename, 'w', encoding='utf8') as fp:
        fp.write('graphemes\tfrequency\tcodepoints\tnames\n')
        for graphemes, frequency in sorted(problem_chars.items()):
            row = [graphemes, str(frequency), ' '.join('U+%04i'% ord(cp) for cp in graphemes),
                   ', '.join(unicodedata.name(cp, 'Unknown codepoint') for cp in graphemes)]
            fp.write('\t'.join(row))
            fp.write('\n')

    good, problems = context_tokenizer.split_problems(tokenized, args['--missing'])

    #successful tokenized words
    filename = root + '_tokenized.tsv'
    with io.open(filename, 'w', encoding='utf8') as fp:
        header = ['originals', 'tokenized']
        if transliterate:
            header.extend(transliterate)
        fp.write('\t'.join(header))
        fp.write('\n')
        for tokenized in good:
            row = [tokenized[0]]
            for transliterated in tokenized[1:]:
                row.append(' '.join(transliterated))
            fp.write('\t'.join(row))
            fp.write('\n')

    #problematic words
    filename = root + '_errors.tsv'
    with io.open(filename, 'w', encoding='utf8') as fp:
        fp.write('originals\ttokenized\n')
        for tokenized in problems:
            fp.write('%s\t%s\n' % (tokenized[0], ' '.join(tokenized[1])))


if __name__ == '__main__':  # pragma: no cover
    main()
