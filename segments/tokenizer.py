# -*- coding: utf-8 -*-
"""
Tokenizer of Unicode characters, grapheme clusters and tailored grapheme clusters
(of orthographies) given an orthography profile.
"""
from __future__ import unicode_literals, division, absolute_import, print_function
import os
import unicodedata
import logging

import regex as re
from six import string_types

from segments.tree import Tree
from segments.util import normalized_rows, normalized_string
from segments import errors


class Profile(object):
    def __init__(self, input_, delimiter='\t'):
        self.graphemes = set()
        self.mappings = {}
        self.column_labels = []
        token_list = []

        if isinstance(input_, string_types):
            input_ = normalized_rows(input_, delimiter=delimiter)

        log = logging.getLogger(__name__)
        for i, tokens in enumerate(input_):
            # deal with the columns header -- should always start with "graphemes" as per
            # the orthography profiles specification
            if i == 0 and tokens[0].lower().startswith("graphemes"):
                self.column_labels = [token.lower() for token in tokens]
                continue
            token_list.append(tokens)
            grapheme = tokens[0]
            # check for duplicates in the orthography profile (fail if dups)
            if grapheme not in self.graphemes:
                self.graphemes.add(grapheme)
            else:
                log.warn(
                    'duplicate grapheme in orthography profile: {0}'.format(grapheme))

            if len(tokens) > 1:
                self.mappings.update({
                    (grapheme, label): token for token, label
                    in zip(tokens, self.column_labels)})
        self.tree = Tree(token_list)

    def __contains__(self, item):
        return item in self.graphemes


class Rules(object):
    def __init__(self, input_, delimiter=','):
        if isinstance(input_, string_types):
            input_ = normalized_rows(input_, delimiter=delimiter)
        self._rules = [(re.compile(rule), replacement) for rule, replacement in input_]

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

    orthography_profile : string (default = None)
        Filename of the a document source-specific orthography profile and rules file.

    orthography_profile_rules : string (default = None)
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
    class to build a trie data structure, which stores the possible Unicode
    character combinations that are specified in the orthography profile
    (i.e. tailored grapheme clusters) that appear in the data source.

    For example, an orthography profile might specify that in source X
    <uu> is a single grapheme (Unicode parlance: tailored grapheme) and
    thererfore it should be chunked as so. Given an orthography profile and
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

    Lastly, the Tokenizer can be used to transformation as specified in an
    orthography rules file. These transformations are specified in a separate
    file from the orthography profile (that specifics the document specific graphemes,
    and possibly their IPA counterparts) and the orthography rules should
    be applied to the output of a grapheme tokenization.

    In an orthography rules file, rules are given in order in regular
    expressions, e.g. this rule replaces a vowel followed by an <n>
    followed by <space> followed by a second vowel with first vowel
    <space> <n> <space> second vowel, e.g.:

    $ ([a|á|e|é|i|í|o|ó|u|ú])(n)(\s)([a|á|e|é|i|í|o|ó|u|ú]), \1 \2 \4

    """
    grapheme_pattern = re.compile("\X", re.UNICODE)

    def __init__(self,
                 profile=None,
                 profile_delimiter='\t',
                 rules=None,
                 rules_delimiter=',',
                 errors_strict=errors.strict,
                 errors_replace=errors.replace,
                 errors_ignore=errors.ignore):
        self.op = Profile(profile, profile_delimiter) if profile else None
        if not rules and profile and isinstance(profile, string_types):
            _rules = os.path.splitext(profile)[0] + '.rules'
            if os.path.exists(_rules):
                rules = _rules
        self._rules = Rules(rules, rules_delimiter) if rules else None
        self._errors = {
            'strict': errors_strict,
            'replace': errors_replace,
            'ignore': errors_ignore,
        }

    def __call__(self,
                 string,
                 column="graphemes",
                 form=None,
                 ipa=False,
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
        if ipa:
            res = self.combine_modifiers(self.grapheme_clusters(string))
        else:
            if self.op:
                res = self.transform(string, column, errors=errors)
            else:
                res = self.grapheme_clusters(string)

        if self._rules:
            res = self.rules(res)

        if form:
            res = normalized_string(res, add_boundaries=False, form=form)
        return res

    def characters(self, string):
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
        return ' '.join(char for char in normalized_string(string))

    def grapheme_clusters(self, string):
        """
        See: Unicode Standard Annex #29: UNICODE TEXT SEGMENTATION
        http://www.unicode.org/reports/tr29/

        Given a string as input, return a space-delimited string of Unicode graphemes
        using the "\X" regular expression.

        Parameters
        ----------
        string : str
            A Unicode string to be tokenized into graphemes.

        Returns
        -------
        result : str
            String returned is space-delimited on Unicode graphemes and contains "#" to
            mark word boundaries.
            The string is in NFD.

        Notes
        -----
        Input is first normalized according to Normalization Ford D(ecomposition).
        """
        # init the regex Unicode grapheme cluster match
        return ' '.join(self.grapheme_pattern.findall(normalized_string(string)))

    def graphemes(self, string, errors='replace'):
        """
        Tokenizes strings given an orthograhy profile that specifies graphemes in a source
        doculect.

        Parameters
        ----------
        string : str
            The str to be tokenized and formatted.

        Returns
        -------
        result : str
            The result of the tokenized and QLC formatted str.

        """
        # if no orthography profile is specified, simply return
        # Unicode grapheme clusters, regex pattern "\X"
        if not self.op:
            return self.grapheme_clusters(string)

        parses = []
        for word in normalized_string(string, add_boundaries=False).split():
            parse = self.op.tree.parse(word)

            # case where the parsing fails
            if not parse:
                # replace characters in string but not in orthography profile with <?>
                parse = " " + self.find_missing_characters(
                    self.characters(word), errors=errors)
            parses.append(parse)

        # remove the outer word boundaries
        return "".join(parses).replace("##", "#").rstrip("#").lstrip("#").strip()

    def transform(self,
                  string,
                  column="graphemes",
                  errors='replace',
                  exception=None,
                  separator=' # '):
        """
        Transform a string's graphemes into the mappings given in a different column
        in the orthography profile. By default this function returns an orthography
        profile grapheme tokenized string.

        Parameters
        ----------
        string : str
            The input string to be tokenized.

        conversion : str (default = "graphemes")
            The label of the column to transform to. Default it to tokenize with
            orthography profile.

        Returns
        -------
        result : str
            Result of the transformation.

        """
        exception = exception or {"#": "#", "?": "?"}

        # This method can't be called unless an orthography profile was specified.
        if not self.op:
            raise ValueError(
                "This method only works when an orthography profile is specified.")

        column = column.lower()
        if column == "graphemes":
            return self.graphemes(string, errors=errors)

        # if the column label for conversion doesn't exist, return grapheme tokenization
        if column not in self.op.column_labels:
            raise ValueError("Column {0} not found in profile.".format(column))

        result = []
        # convert string to raw string to allow for parsing of backslashes
        for part in string.split(' '):
            out = []
            for token in self.graphemes(r'' + part, errors=errors).split(' '):
                target = (
                    exception.get(token) or
                    self.op.mappings.get((token, column)) or
                    self._errors['replace'](token))
                if target != "NULL":
                    # result.append(self.mappings[token, column])
                    out.append(target)
            result.append(' '.join(out))

        return separator.join(result).strip()

    def transform_rules(self, string):
        """
        Convenience function that first tokenizes a string into orthographic profile-
        specified graphemes and then applies the orthography profile rules.
        """
        return self.rules(self.transform(string))

    def rules(self, string):
        """
        Function to tokenize input string and return output of str with ortho rules
        applied.

        Parameters
        ----------
        string : str
            The input string to be tokenized.

        Returns
        -------
        result : str
            Result of the orthography rules applied to the input str.

        """
        # if no orthography profile rules file has been specified, simply return the
        # string
        if not self._rules:
            return string

        result = self._rules.apply(normalized_string(string, add_boundaries=False))

        # this is in case someone introduces a non-NFD ordered sequence of characters
        # in the orthography profile
        return normalized_string(result, add_boundaries=False)

    def find_missing_characters(self, char_tokenized_string, errors='replace'):
        """
        Given a string tokenized into characters, return a characters
        tokenized string where each character missing from the orthography
        profile is replaced with a question mark <?>.
        """
        error = self._errors[errors]
        return " ".join(
            [c if c in self.op else error(c) for c in char_tokenized_string.split()])

    def combine_modifiers(self, string):
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
        graphemes = string.split()
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
        return " ".join(r)
