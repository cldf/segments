# -*- coding: utf-8 -*-
"""
Tokenizer of Unicode characters, grapheme clusters and tailored grapheme clusters
(of orthographies) given an orthography profile.
"""
from __future__ import unicode_literals, division, absolute_import, print_function
import os
import unicodedata
import logging
from collections import Counter, OrderedDict

import regex as re
from six import string_types
from clldutils.path import readlines
from clldutils.dsv import reader
from clldutils.misc import UnicodeMixin

from segments.tree import Tree
from segments.util import nfd, NULL
from segments import errors

logging.basicConfig()

GRAPHEME_COL = 'Grapheme'


class Profile(UnicodeMixin):
    def __init__(self, *specs):
        self.graphemes = []
        self.mappings = {}
        self.column_labels = []

        log = logging.getLogger(__name__)
        for i, spec in enumerate(specs):
            if not self.column_labels:
                self.column_labels = list(spec.keys())

            if 'Grapheme' not in spec:
                raise ValueError('invalid grapheme specification')

            grapheme = spec[GRAPHEME_COL]
            # check for duplicates in the orthography profile (fail if dups)
            if grapheme not in self.graphemes:
                self.graphemes.append(grapheme)
            else:
                log.warn(
                    'line {0}:duplicate grapheme in profile: {1}'.format(i + 2, grapheme))
            self.mappings.update(
                {(grapheme, k): v for k, v in spec.items() if k != GRAPHEME_COL})
        self.tree = Tree(self.graphemes)

    @classmethod
    def from_file(cls, fname):
        """
        Orthography profiles must be
        - tab-separated CSV files
        - encoded in UTF-8
        - with a header containing a column "Grapheme"
        """
        return cls(*list(
            reader(readlines(fname, normalize='NFD'), dicts=True,
                delimiter='\t', quotechar=None)))

    @classmethod
    def from_text(cls, text, mapping='mapping'):
        graphemes = Counter(Tokenizer.grapheme_pattern.findall(nfd(text)))
        specs = [
            OrderedDict([
                (GRAPHEME_COL, grapheme),
                ('frequency', frequency),
                (mapping, grapheme)])
            for grapheme, frequency in graphemes.most_common()]
        return cls(*specs)

    @classmethod
    def from_textfile(cls, fname, mapping='mapping'):
        return cls.from_text(' '.join(readlines(fname)), mapping=mapping)

    def __unicode__(self):
        rows = [[GRAPHEME_COL] + ['%s' % col for col in self.column_labels
                                  if col != GRAPHEME_COL]]
        for grapheme in self.graphemes:
            rows.append(
                [grapheme] +
                ['%s' % self.mappings[grapheme, col]
                 for col in self.column_labels if col != GRAPHEME_COL])
        return '\n'.join('\t'.join(row) for row in rows)


class Rules(object):
    """
    Rules are given in tuple format, comma delimited.
    Regular expressions are given in Python syntax.
    """
    def __init__(self, *rules):
        self._rules = [(re.compile(rule), replacement) for rule, replacement in rules]

    @classmethod
    def from_file(cls, fname):
        return cls(*list(reader(readlines(fname, comment='#', normalize='NFD'))))

    def apply(self, s):
        for rule, replacement in self._rules:
            s = rule.sub(replacement, s)
        return s


class Tokenizer(object):
    """
    Class for Unicode character and grapheme tokenization.

    This class provides extended functionality for
    orthography-specific tokenization with orthography profiles.

    Parameters
    ----------

    profile : string (default = None)
        Filename of the a document source-specific orthography profile and rules file.

    rules : string (default = None)
        Filename of the a document source-specific orthography profile rules file.

    Notes
    -----
    The tokenizer can be used for pure Unicode character and grapheme
    tokenization, i.e. it uses the Unicode standard grapheme parsing rules, as
    implemented in the Python regex package by Matthew Barnett, to do basic tokenization
    with the "\X" grapheme regular expression match. This grapheme match
    combines one or more Combining Diacritical Marks to their base character.
    These are called "grapheme clusters" in Unicode parlance. With these functions
    the Tokenizer is meant to do basic rudimentary parsing for things like generating
    unigram models (segments and their counts) from input data.

    The Tokenizer reads in an orthography profile and calls a helper
    class to build a tree data structure, which stores the possible Unicode
    character combinations that are specified in the orthography profile
    (i.e. tailored grapheme clusters) that appear in the data source.

    For example, an orthography profile might specify that in source X
    <uu> is a single grapheme (Unicode parlance: tailored grapheme) and
    therefore it should be chunked as so. Given an orthography profile and
    some data to tokenize, the process would look like this:

    input string example: uubo uubo
    output string example: uu b o # uu b o

    See also the test orthography profile and rules in the test directory.

    An additional method "combine_modifiers" handles the case where there are
    Unicode Spacing Modifier Letters, which are not explicitly
    combined to their base character in the Unicode Standard. These graphemes
    are called "Tailored grapheme clusters" in Unicode. For more information
    see the Unicode Standard Annex #29: Unicode Text Segmentation:

    * http://www.unicode.org/reports/tr29/

    Additionally, the Tokenizer provides functionality to transform graphemes
    into associated character(s) specified in additional columns in the orthography
    profile. A dictionary is created that keeps a mapping between source-specific
    graphemes and their counterparts (e.g. an IPA column in the orthography profile).

    Lastly, the Tokenizer can be used to transform text as specified in an
    orthography rules file. These transformations are specified in a separate
    file from the orthography profile (that specifics the document specific graphemes,
    and possibly their IPA counterparts) and the orthography rules should
    be applied to the output of a grapheme tokenization.

    In an orthography rules file, rules are given in order in regular
    expressions, e.g. this rule replaces a vowel followed by an <n>
    followed by <space> followed by a second vowel with first vowel
    <space> <n> <space> second vowel, e.g.::

        $ (a|á|e|é|i|í|o|ó|u|ú)(n)(\s)(a|á|e|é|i|í|o|ó|u|ú), \1 \2 \4

    """
    grapheme_pattern = re.compile("\X", re.UNICODE)

    def __init__(self,
                 profile=None,
                 rules=None,
                 errors_strict=errors.strict,
                 errors_replace=errors.replace,
                 errors_ignore=errors.ignore):
        self.op = None
        if isinstance(profile, Profile):
            self.op = profile
        elif profile is not None:
            self.op = Profile.from_file(profile)
        if not rules and profile and isinstance(profile, string_types):
            _rules = os.path.splitext(profile)[0] + '.rules'
            if os.path.exists(_rules):
                rules = _rules
        self._rules = Rules.from_file(rules) if rules else None
        self._errors = {
            'strict': errors_strict,
            'replace': errors_replace,
            'ignore': errors_ignore,
        }

    def __call__(self,
                 string,
                 column=GRAPHEME_COL,
                 form=None,
                 ipa=False,
                 segment_separator=' ',
                 separator=' # ',
                 errors='replace'):
        """
        The main task of a Tokenizer is tokenizing! This is what happens when called.

        This function determines what to do given any combination
        of orthography profiles and rules or not orthography profiles
        or rules.

        Parameters
        ----------
        string : str
            The input string to be tokenized.

        column : str (default = "graphemes")
            The column label for the transformation, if specified.

        form : None or unicode normalization form
            Normalize return value if form is not None.

        ipa : bool
            Tokenize IPA (work in progress)

        Returns
        -------
        result : str
            Result of the tokenization.

        """
        res = []
        for word in nfd(string).split():
            if ipa:
                res.append(self.combine_modifiers(self.grapheme_clusters(word)))
            else:
                if self.op:
                    res.append(
                        self.transform(word, column=column, error=self._errors[errors]))
                else:
                    res.append(self.grapheme_clusters(word))

        def pp(word):
            res = segment_separator.join(word).strip()
            res = self._rules.apply(res) if self._rules else res
            return unicodedata.normalize(form, res) if form else res

        return separator.join(pp(word) for word in res)

    def characters(self, string, segment_separator=' ', separator=' # ',):
        """
        Given a string as input, return a space-delimited string of Unicode characters
        (code points rendered as glyphs).
        Parameters
        ----------
        string : str
            A Unicode string to be tokenized into graphemes.
        Returns
        -------
        result : str
            String returned is space-delimited on Unicode characters and contains "#" to
            mark word boundaries.
            The string is in NFD.
        Notes
        -----
        Input is first normalized according to Normalization Ford D(ecomposition).
        String returned contains "#" to mark word boundaries.
        """
        return separator.join(segment_separator.join(word) for word in nfd(string).split())

    def grapheme_clusters(self, word):
        """
        See: Unicode Standard Annex #29: UNICODE TEXT SEGMENTATION
        http://www.unicode.org/reports/tr29/

        Given a string as input, return a list of Unicode graphemes using the
        "\X" regular expression.

        Parameters
        ----------
        word : str
            A Unicode string to be tokenized into graphemes.

        Returns
        -------
        result : list
            List of Unicode graphemes in NFD.

        """
        # init the regex Unicode grapheme cluster match
        return self.grapheme_pattern.findall(word)

    def transform(self, word, column=GRAPHEME_COL, error=errors.replace):
        """
        Transform a string's graphemes into the mappings given in a different column
        in the orthography profile.

        Parameters
        ----------
        word : str
            The input string to be tokenized.

        column : str (default = "Grapheme")
            The label of the column to transform to. Default it to tokenize with
            orthography profile.

        Returns
        -------
        result : list of lists
            Result of the transformation.

        """
        assert self.op, 'method can only be called with orthography profile.'

        if column not in self.op.column_labels:
            raise ValueError("Column {0} not found in profile.".format(column))

        word = self.op.tree.parse(word, error)
        if column == GRAPHEME_COL:
            return word
        out = []
        for token in word:
            target = (
                self.op.mappings.get((token, column)) or
                self._errors['replace'](token))
            if target != NULL:
                # FIXME: should compare against respective column description in the
                # profile metadata!
                if isinstance(target, (tuple, list)):
                    out.extend(target)
                else:
                    out.append(target)
        return out

    def rules(self, word):
        """
        Function to tokenize input string and return output of str with ortho rules
        applied.

        Parameters
        ----------
        word : str
            The input string to be tokenized.

        Returns
        -------
        result : str
            Result of the orthography rules applied to the input str.

        """
        return self._rules.apply(word) if self._rules else word

    def combine_modifiers(self, graphemes):
        """
        Given a string that is space-delimited on Unicode grapheme clusters,
        group Unicode modifier letters with their preceding base characters,
        deal with tie bars, etc.

        Parameters
        ----------
        string : str
            A Unicode string tokenized into grapheme clusters to be tokenized into simple
            IPA.

        """
        result = []
        temp = ""
        count = len(graphemes)
        for grapheme in reversed(graphemes):
            count -= 1
            if len(grapheme) == 1 and unicodedata.category(grapheme) == "Lm" \
                    and not ord(grapheme) in [712, 716]:
                temp = grapheme + temp
                # hack for the cases where a space modifier is the first character in the
                # string
                if count == 0:
                    result[-1] = temp + result[-1]
                continue  # pragma: no cover
            # catch and repair stress marks
            if len(grapheme) == 1 and ord(grapheme) in [712, 716]:
                result[-1] = grapheme + result[-1]
                temp = ""
                continue

            # combine contour tone marks (non-accents)
            if len(grapheme) == 1 and unicodedata.category(grapheme) == "Sk":
                if len(result) == 0:
                    result.append(grapheme)
                    temp = ""
                    continue
                else:
                    if unicodedata.category(result[-1][0]) == "Sk":
                        result[-1] = grapheme + result[-1]
                        temp = ""
                        continue

            result.append(grapheme + temp)
            temp = ""

        # last check for tie bars
        segments = result[::-1]
        i = 0
        r = []
        while i < len(segments):
            # tie bars
            if ord(segments[i][-1]) in [865, 860]:
                r.append(segments[i] + segments[i + 1])
                i += 2
            else:
                r.append(segments[i])
                i += 1
        return r
