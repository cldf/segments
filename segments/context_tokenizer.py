# -*- coding: utf-8 -*-
"""Implementation of several segmentation strategies for unicode strings based
on a 'profile' as additional input. A profile contains a list of rules and
a matching rule on a substring leads to marking this substring as a segment.
"""

from __future__ import unicode_literals, division, absolute_import, print_function
import sys
import csv
import collections
import unicodedata
import regex as re
from io import open
from collections import defaultdict

# flake8: noqa

PY3 = sys.version_info > (3,)
if PY3:
    xrange = range


class Profile(object):
    def __init__(self, fieldnames, patterns):
        self.fieldnames = fieldnames
        self.patterns = patterns


    def sort(self, sort_by):
        """sort profile by given criteria"""

        #depends on sort being stable (guaranteed since python 2.3)
        patterns = self.patterns
        for criterium in reversed(sort_by):
            if criterium == 'reverse':
                patterns.reverse()
            elif criterium == 'context':
                patterns.sort(key=lambda x: 0 if len(x.left) + len(x.right) == 0 else -1)
            elif criterium == 'size':
                patterns.sort(key=lambda x: -len(x.graphemes))
            else:
                print('Skipping unknown sort criterium "%s"' % criterium, file=sys.stderr)


    def save(self, fp):
        header = ['frequency']
        header.extend(self.fieldnames)
        fp.write('\t'.join(header))
        fp.write('\n')
        for p in self.patterns:
            row = [str(p.frequency)]
            for name in self.fieldnames:
                row.append(p.defining_dict[name])
            fp.write('\t'.join(row))
            fp.write('\n')


    def normalize(self, norm_form):
        for p in self.patterns:
            p.normalize(norm_form)


    def prepare_regex(self, ignore_case):
        flags = re.VERSION1
        if ignore_case:
            flags |= re.IGNORECASE

        for pattern in self.patterns:
            pattern.prepare_regex(flags)

    def prepare_simple(self, ignore_case):
        for pattern in self.patterns:
            pattern.prepare_simple(ignore_case)


    @staticmethod
    def read_profile(filename):
        patterns = []
        klasses = defaultdict(list)
        if PY3:
            fp = open(filename, newline='')
            reader = csv.DictReader((row for row in fp if not row.startswith('#')),
                                    delimiter='\t')
        else:
            fp = open(filename, 'rb')
            reader = csv.DictReader((row for row in fp if not row.startswith(str('#'))),
                                    delimiter=str('\t'))
        for row in reader:
            for key in row:
                if row[key] is None:
                    row[key] = ''
                elif not PY3:
                    row[key] = unicode(row[key], 'utf8')
            pattern = Pattern(row)
            patterns.append(pattern)
            if pattern.klass:
                klasses[pattern.klass].append(pattern)
        fp.close()

        for k in klasses:
            klasses[k] = '((' + ')|('.join(p.graphemes for p in klasses[k]) + '))'
        for pattern in patterns:
            pattern.substituteClasses(klasses)

        return Profile(reader.fieldnames, patterns)


    @staticmethod
    def create_profile(filename, profile_filename, normalize=None, simple=False, comment_sign='#'):
        graphemes = collections.Counter()
        grapheme_pattern = re.compile(r'\X', re.UNICODE)
        with open(filename, encoding='utf8') as wordlist_fp:
            if normalize is None:
                line_iter = (line.rstrip() for line in wordlist_fp if not line.startswith(comment_sign))
            else:
                line_iter = iter_normalized(wordlist_fp, normalize, comment_sign)
            for line in line_iter:
                graphemes.update(grapheme_pattern.findall(line))
        with open(profile_filename, 'w', encoding='utf8') as profile_fp:
            if simple:
                profile_fp.write('frequency\tgraphemes\n')
                for grapheme, count in graphemes.most_common():
                    profile_fp.write('%7d\t%s\n' % (count, grapheme))
            else:
                profile_fp.write('frequency\tleft\tgraphemes\tright\tcodepoints\tnames\n')
                for grapheme, count in graphemes.most_common():
                    codepoints = ' '.join('U+%04i'% ord(cp) for cp in grapheme)
                    names = ', '.join(unicodedata.name(cp, 'Unknown codepoint') for cp in grapheme)
                    profile_fp.write('%7d\t\t%s\t%s\t%s\n' % (count, grapheme, codepoints, names))


class Pattern(object):
    def __init__(self, row):
        self.defining_dict = row

        # left context of pattern definition
        self.left = row.get('left', '').strip()
        self._left = self.left # this.left modified by class definitions in profile
        self.c_left = None # compiled regex

        # central part of the pattern
        self.graphemes = row.get('graphemes', '').strip()
        self.c_graphemes = None # compiled regex

        # right context
        self.right = row.get('right', '').strip()
        self._right = self.right # this.right modified by class definitions in profile
        self.c_right = None # compiled regex

        self.klass = row.get('class', '').strip()
        self.frequency = int(row.get('frequency', '0').strip())


    def substituteClasses(self, klasses):
        for k in klasses:
            if k in self._left:
                self._left = self._left.replace(k, klasses[k])
            if k in self._right:
                self._right = self._right.replace(k, klasses[k])


    def normalize(self, form):
        assert form in ('NFC', 'NFD', 'NFKC', 'NFKD')
        self.left = unicodedata.normalize(form, self.left)
        self._left = unicodedata.normalize(form, self._left)
        self.graphemes = unicodedata.normalize(form, self.graphemes)
        self.right = unicodedata.normalize(form, self.right)
        self._right = unicodedata.normalize(form, self.right)
        self.klass = unicodedata.normalize(form, self.klass)


    def prepare_regex(self, flags):
        self.c_left = re.compile(self._left + '$', flags)
        self.c_graphemes = re.compile(self.graphemes, flags)
        self.c_right = re.compile(self._right, flags)


    def prepare_simple(self, ignore_case):
        if ignore_case:
            self.c_graphemes = self.graphemes.lower()
        else:
            self.c_graphemes = self.graphemes


def iter_normalized(words, form, comment_sign='#'):
    assert form in ('NFC', 'NFD', 'NFKC', 'NFKD')
    for w in words:
        w = w.strip()
        if not w or comment_sign and w[0] == comment_sign:
            continue
        yield unicodedata.normalize(form, w)



def split_problems(tokenized, missing=u'\u2047'):
    good = []
    problems = []
    for t in tokenized:
        if missing in t[1]:
            problems.append(t)
        else:
            good.append(t)
    return good, problems


# now follow the different segmentation algorithms
# I went for some code duplication in favour of trying to merge everything in one
# function, which IMO would blow up code complexity too much.

def tokenize_linear(words, profile, transliterate=None, use_context=False, ignore_case=False, missing=u'\u2047',
                    match_logger=None):
    """
    Iterate over the word from left to right and find the first matching pattern in the profile.

    Parameters
    ----------
    words: some Iterable over strings
    profile: Profile instance
    transliterate: List
        list of column names where each one has to exist in the profile
    use_context: bool
        use the context from the profile to define matchings
        default: False
    ignore_case: bool
        When matching, take character case into account or not
        default: False
    missing: String
        String to insert into segmentation if a unicode codepoint couldn't
        be matched
        default: '\u2047'
    match_logger: file object for logging of matched patterns
        default: None

    Returns
    -------
    tokenized_list: list of lists
        for every word in words returns a list of the form [original_word, tokenized_word, transliterated1, ... ]
    """

    profile.prepare_regex(ignore_case)

    tokenized = []
    problems = defaultdict(int)
    zero_length_matching = collections.OrderedDict()
    for word in words:
        run = 0
        end = len(word)
        row = [word, []]
        if transliterate:
            for _ in transliterate:
                row.append([])
        tokenized.append(row)
        if match_logger:
            match_logger.write('%s\n' % word)
        while run < end:
            for pattern in profile.patterns:
                match = pattern.c_graphemes.match(word, run)
                if not match:
                    continue
                if len(match.group()) == 0:
                    zero_length_matching[pattern] = True
                    continue
                if use_context:
                    pre_match = pattern.c_left.search(word, 0, match.start())
                    if not pre_match:
                        continue
                    post_match = pattern.c_right.match(word, match.end())
                    if not post_match:
                        continue
                row[1].append(match.group())
                if transliterate:
                    for index, key in enumerate(transliterate):
                        row[index+2].append(pattern.defining_dict[key])
                run = match.end()
                pattern.frequency += 1
                if match_logger:
                    match_logger.write('\t%s\t%s %s %s\n' %
                                       (match.group(), pattern.left, pattern.graphemes, pattern.right))
                break
            else:
                row[1].append(missing)
                if transliterate:
                    for index, key in enumerate(transliterate):
                        row[index+2].append(missing)
                problems[word[run]] += 1
                if match_logger:
                    match_logger.write('\t%s\t%s\n' % (word[run], missing))
                run += 1
    for pattern in zero_length_matching:
        print("Warning: The following row produces zero-length matches:\n\t%s" % pattern.defining_dict,
              file=sys.stderr)
    return tokenized, problems


def tokenize_global(words, profile, transliterate=None, use_context=False, ignore_case=False, missing=u'\u2047',
                    match_logger=None):
    """
    Iterate over patterns in the profile and find matches in the word. Once parts are matched they aren't taken
    into consideration for other matches.

    Parameters
    ----------
    words: some Iterable over strings
    profile: Profile instance
    transliterate: List
        list of column names where each one has to exist in the profile
    use_context: bool
        use the context from the profile to define matchings
        default: False
    ignore_case: bool
        When matching, take character case into account or not
        default: False
    missing: String
        String to insert into segmentation if a unicode codepoint couldn't
        be matched
        default: '\u2047'
    match_logger: file object for logging of matched patterns
        default: None

    Returns
    -------
    tokenized_list: list of lists
        for every word in words returns a list of the form [original_word, tokenized_word, transliterated1, ... ]
    """

    profile.prepare_regex(ignore_case)

    tokenized = []
    problems = defaultdict(int)
    for word in words:
        matches = dict()
        done = set()
        for pattern in profile.patterns:
            have_zero_length_matches = False
            for match in pattern.c_graphemes.finditer(word):
                have_zero_length_matches = have_zero_length_matches or len(match.group()) == 0
                if any(x in done for x in xrange(match.start(), match.end())) or len(match.group()) == 0:
                    continue
                if use_context:
                    pre_match = pattern.c_left.search(word, 0, match.start())
                    if not pre_match:
                        continue
                    post_match = pattern.c_right.match(word, match.end())
                    if not post_match:
                        continue
                for x in xrange(match.start(), match.end()):
                    done.add(x)
                matches[match.start()] = (match, pattern)
            if have_zero_length_matches:
                print("Warning: The following row produces zero-length matches:\n\t%s" % pattern.defining_dict,
                      file=sys.stderr)
        row = [word, []]
        tokenized.append(row)
        if transliterate:
            for _ in transliterate:
                row.append([])
        run = 0
        end = len(word)
        if match_logger:
            match_logger.write('%s\n' % word)
        while run < end:
            if run in matches:
                match, pattern = matches[run]
                pattern.frequency += 1
                row[1].append(match.group())
                if transliterate:
                    for index, key in enumerate(transliterate):
                        row[index+2].append(pattern.defining_dict[key])
                run = match.end()
                if match_logger:
                    match_logger.write('\t%s\t%s %s %s\n' %
                                       (match.group(), pattern.left, pattern.graphemes, pattern.right))
            else:
                row[1].append(missing)
                if transliterate:
                    for index, key in enumerate(transliterate):
                        row[index+2].append(missing)
                problems[word[run]] += 1
                if match_logger:
                    match_logger.write('\t%s\t%s\n' % (word[run], missing))
                run += 1

    return tokenized, problems


def tokenize_linear_simple(words, profile, transliterate=False, ignore_case=False, missing=u'\u2047'):
    """
    Iterate over the word from left to right and find the first matching pattern in the profile. Use a simple
    algorithm, which disallows regular expressions and contexts.


    Parameters
    ----------
    words: some Iterable over strings
    profile: Profile instance
    transliterate: List
        list of column names where each one has to exist in the profile
    ignore_case: bool
        When matching, take character case into account or not
        default: False
    missing: String
        String to insert into segmentation if a unicode codepoint couldn't
        be matched
        default: '\u2047'

    Returns
    -------
    tokenized_list: list of lists
        for every word in words returns a list of the form [original_word, tokenized_word, transliterated1, ... ]
    """

    profile.prepare_simple(ignore_case)

    tokenized = []
    problems = defaultdict(int)
    for word in words:
        run = 0
        end = len(word)
        row = [word, []]
        if transliterate:
            for _ in transliterate:
                row.append([])
        tokenized.append(row)
        if ignore_case:
            working_word = word.lower()
        else:
            working_word = word
        while run < end:
            for pattern in profile.patterns:
                if not working_word.startswith(pattern.c_graphemes, run):
                    continue
                if transliterate:
                    for index, key in enumerate(transliterate):
                        row[index+2].append(pattern.defining_dict[key])
                run += len(pattern.c_graphemes)
                pattern.frequency += 1
                break
            else:
                row[1].append(missing)
                if transliterate:
                    for index, key in enumerate(transliterate):
                        row[index+2].append(missing)
                problems[word[run]] += 1
                run += 1
    return tokenized, problems


def tokenize_global_simple(words, profile, transliterate=None, ignore_case=False, missing=u'\u2047'):
    """
    Iterate over patterns in the profile and find matches in the word. Once parts are matched they aren't taken
    into consideration for other matches. Use a simple algorithm, which disallows regular expressions and contexts.

    Parameters
    ----------
    words: some Iterable over strings
    profile: Profile instance
    transliterate: List
        list of column names where each one has to exist in the profile
    ignore_case: bool
        When matching, take character case into account or not
        default: False
    missing: String
        String to insert into segmentation if a unicode codepoint couldn't
        be matched
        default: '\u2047'

    Returns
    -------
    tokenized_list: list of lists
        for every word in words returns a list of the form [original_word, tokenized_word, transliterated1, ... ]
    """

    profile.prepare_simple(ignore_case)

    tokenized = []
    problems = defaultdict(int)
    for word in words:
        if ignore_case:
            working_word = word.lower()
        else:
            working_word = word
        matches = dict()
        done = set()
        for pattern in profile.patterns:
            run = 0
            end = len(working_word)
            while run < end:
                index = working_word.find(pattern.c_graphemes, run)
                if index == -1:
                    break
                run = index+1
                if any(x in done for x in xrange(index, index+len(pattern.c_graphemes))):
                    continue
                for x in xrange(index, index+len(pattern.c_graphemes)):
                    done.add(x)
                matches[index] = (word[index:index+len(pattern.c_graphemes)], pattern)
        row = [word, []]
        tokenized.append(row)
        if transliterate:
            for _ in transliterate:
                row.append([])
        run = 0
        end = len(word)
        while run < end:
            if run in matches:
                match, pattern = matches[run]
                pattern.frequency += 1
                row[1].append(match)
                if transliterate:
                    for index, key in enumerate(transliterate):
                        row[index+2].append(pattern.defining_dict[key])
                run = run + len(match)
            else:
                row[1].append(missing)
                if transliterate:
                    for index, key in enumerate(transliterate):
                        row[index+2].append(missing)
                problems[word[run]] += 1
                run += 1

    return tokenized, problems
