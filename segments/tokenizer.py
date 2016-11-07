# -*- coding: utf-8 -*-
"""
Tokenizer of Unicode characters, grapheme clusters and tailored grapheme clusters (of orthographies) given an orthography profile.  
"""
from __future__ import unicode_literals, division, absolute_import, print_function
import os
import unicodedata
import regex as re
from six import text_type

from segments.tree import Tree
from segments.util import normalized_rows, normalized_string


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

    def __init__(self, orthography_profile=None,
            orthography_profile_rules=None, delimiter='\t'):
        if not orthography_profile:
            self.orthography_profile = None
            self._data = None
        elif isinstance(orthography_profile, text_type):
            self.orthography_profile = orthography_profile
            self._data = list(normalized_rows(orthography_profile, delimiter))
        else:
            self.orthography_profile = 'custom'
            self._data = orthography_profile
        
        self.orthography_profile_rules = orthography_profile_rules
        self.tree = None

        # store column labels from the orthography profile
        self.column_labels = []

        # look up table of graphemes to other column transforms
        self.mappings = {}

        # double check that there are no duplicate graphemes in the orthography profile
        self.op_graphemes = {}

        # orthography profile processing
        if self.orthography_profile:
            
            # read in orthography profile and create a trie structure for tokenization
            self.tree = Tree(self._data)
            # process the orthography profiles and rules
            self._init_profile()

        if not self.orthography_profile_rules and self.orthography_profile:
            rules_path = os.path.splitext(self.orthography_profile)[0] + '.rules'
            if os.path.exists(rules_path):
                self.orthography_profile_rules = rules_path

        # orthography profile rules and replacements
        if self.orthography_profile_rules:
            self.op_rules = []
            for rule, replacement in normalized_rows(self.orthography_profile_rules, ','):
                self.op_rules.append((re.compile(rule), replacement))

    def _init_profile(self):
        """
        Process and initialize data structures given an orthography profile.
        """
        for tokens in self._data:
            # deal with the columns header -- should always start with "graphemes" as per the orthography profiles specification
            if tokens[0].lower().startswith("graphemes"):
                self.column_labels.extend([token.lower() for token in tokens])
                continue

            grapheme = tokens[0]

            # check for duplicates in the orthography profile (fail if dups)
            if grapheme not in self.op_graphemes:
                self.op_graphemes[grapheme] = 1
            else:
                raise Exception("{0} is duplicate in your orthography profile.".format(grapheme))

            if len(tokens) == 1:
                continue

            self.mappings.update(
                {(grapheme, label): token
                 for token, label in zip(tokens, self.column_labels)})

    def characters(self, string):
        """
        Given a string as input, return a space-delimited string of Unicode characters (code points rendered as glyphs).

        Parameters
        ----------
        string : str
            A Unicode string to be tokenized into graphemes.

        Returns
        -------
        result : str
            String returned is space-delimited on Unicode characters and contains "#" to mark word boundaries.
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

        Given a string as input, return a space-delimited string of Unicode graphemes using the "\X" regular expression.

        Parameters
        ----------
        string : str
            A Unicode string to be tokenized into graphemes.

        Returns
        -------
        result : str
            String returned is space-delimited on Unicode graphemes and contains "#" to mark word boundaries.
            The string is in NFD.

        Notes
        -----
        Input is first normalized according to Normalization Ford D(ecomposition).
        """
        # init the regex Unicode grapheme cluster match
        return ' '.join(self.grapheme_pattern.findall(normalized_string(string)))

    def graphemes(self, string, missing="?"):
        """
        Tokenizes strings given an orthograhy profile that specifies graphemes in a source doculect.

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
        if not self.orthography_profile:
            return self.grapheme_clusters(string)

        parses = []
        for word in normalized_string(string, add_boundaries=False).split():
            parse = self.tree.parse(word)
            # case where the parsing fails
            if not parse:
                # replace characters in string but not in orthography profile with <?>
                parse = " " + self.find_missing_characters(self.characters(word),
                        missing=missing)
            parses.append(parse)

        # remove the outer word boundaries
        return "".join(parses).replace("##", "#").rstrip("#").lstrip("#").strip()

    def _search_graphemes(self, string, _missing='???'):
        """Helper function to parse graphemes, including missing ones."""
        graphemes = self.graphemes(string, missing=_missing)
        if not _missing in graphemes.split(' '):
            return graphemes
        out = []
        rest = string
        while rest:
            best_idx = 1
            best_match = rest[:best_idx]
            for i in range(1, len(rest)):
                new_string = rest[:i]
                new_parse = self.graphemes(new_string, missing=_missing)
                if not _missing in new_parse.split(' '):
                    best_idx = i
                    best_match = new_parse
            out += [best_match]
            rest = rest[best_idx:]
        return ' '.join(out) 

    def transform(self, string, column="graphemes", exception=None,
            missing=None, _missing='???', separator=' # '):
        """
        Transform a string's graphemes into the mappings given in a different column
        in the orthography profile. By default this function returns an orthography
        profile grapheme tokenized string.

        Parameters
        ----------
        string : str
            The input string to be tokenized.

        conversion : str (default = "graphemes")
            The label of the column to transform to. Default it to tokenize with orthography profile.

        Returns
        -------
        result : str
            Result of the transformation.

        """
        column = column.lower()
        exception = exception or {"#": "#", "?": "?"}
        if not missing:
            missing = lambda x: '<{0}>'.format(x)

        # This method can't be called unless an orthography profile was specified.
        if not self.orthography_profile:
            raise Exception("This method only works when an orthography profile is specified.")

        if column == "graphemes":
            return self._search_graphemes(string, _missing=missing)

        # if the column label for conversion doesn't exist, return grapheme tokenization
        if column not in self.column_labels:
            raise ValueError("Column {0} not found in profile.".format(column)) 

        result = []
        # convert string to raw string to allow for parsing of backslashes
        for part in string.split(' '):
            out = []
            for token in self._search_graphemes(r''+part, _missing=_missing).split(' '):
                target = (
                        exception.get(token) or \
                                self.mappings.get((token, column)) or \
                                missing(token)
                                )
                if target != "NULL":
                    # result.append(self.mappings[token, column])
                    out.append(target)
            result.append(' '.join(out))

        return separator.join(result).strip()

    def tokenize(self, string, column="graphemes"):
        """
        This function determines what to do given any combination
        of orthography profiles and rules or not orthography profiles
        or rules.

        Parameters
        ----------
        string : str
            The input string to be tokenized.

        column : str (default = "graphemes")
            The column label for the transformation, if specified.

        Returns
        -------
        result : str
            Result of the tokenization.

        """
        if self.orthography_profile and self.orthography_profile_rules:
            return self.rules(self.transform(string, column))

        if not self.orthography_profile and not self.orthography_profile_rules:
            return self.grapheme_clusters(string)

        if self.orthography_profile and not self.orthography_profile_rules:
            return self.transform(string, column)

        # it's not yet clear what the order for this procedure should be
        if not self.orthography_profile and self.orthography_profile_rules:
            return self.rules(self.grapheme_clusters(string))

    def transform_rules(self, string):
        """
        Convenience function that first tokenizes a string into orthographic profile-
        specified graphemes and then applies the orthography profile rules.
        """
        return self.rules(self.transform(string))

    def rules(self, string):
        """
        Function to tokenize input string and return output of str with ortho rules applied.

        Parameters
        ----------
        string : str
            The input string to be tokenized.

        Returns
        -------
        result : str
            Result of the orthography rules applied to the input str.

        """
        # if no orthography profile rules file has been specified, simply return the string
        if not self.orthography_profile_rules:
            return string

        result = normalized_string(string, add_boundaries=False)
        for rule, replacement in self.op_rules:
            result = rule.sub(replacement, result)

        # this is in case someone introduces a non-NFD ordered sequence of characters
        # in the orthography profile
        return normalized_string(result, add_boundaries=False)

    def find_missing_characters(self, char_tokenized_string, missing="?"):
        """
        Given a string tokenized into characters, return a characters
        tokenized string where each character missing from the orthography
        profile is replaced with a question mark <?>.
        """
        return " ".join(
            [c if c in self.op_graphemes else missing for c in char_tokenized_string.split()])

    def tokenize_ipa(self, string):
        """
        Work in progress method for tokenizing IPA.
        """
        return self.combine_modifiers(self.grapheme_clusters(string))

    def combine_modifiers(self, string):
        """
        Given a string that is space-delimited on Unicode grapheme clusters,
        group Unicode modifier letters with their preceding base characters,
        deal with tie bars, etc.

        Parameters
        ----------
        string : str
            A Unicode string tokenized into grapheme clusters to be tokenized into simple IPA.

        """
        result = []
        graphemes = string.split()
        temp = ""
        count = len(graphemes)
        for grapheme in reversed(graphemes):
            count -= 1
            if len(grapheme) == 1 and unicodedata.category(grapheme) == "Lm" and not ord(grapheme) in [712, 716]:
                temp = grapheme+temp
                # hack for the cases where a space modifier is the first character in the string
                if count == 0:
                    result[-1] = temp+result[-1]
                continue
            # catch and repair stress marks
            if len(grapheme) == 1 and ord(grapheme) in [712, 716]:
                result[-1] = grapheme+result[-1]
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
                        result[-1] = grapheme+result[-1]
                        temp = ""
                        continue

            result.append(grapheme+temp)
            temp = ""

        # last check for tie bars
        segments = result[::-1]
        i = 0
        r = []
        while i < len(segments):
            # tie bars
            if ord(segments[i][-1]) in [865, 860]:
                r.append(segments[i]+segments[i+1])
                i = i+2
            else:
                r.append(segments[i])
                i += 1
        return " ".join(r)
