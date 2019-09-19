import logging
from collections import Counter, OrderedDict
import unicodedata
from pathlib import Path

from csvw import TableGroup, Column
from clldutils.path import readlines

from segments.tree import Tree
from segments.util import grapheme_pattern

try:  # pragma: no cover
    from json.decoder import JSONDecodeError
except ImportError:  # pragma: no cover
    JSONDecodeError = ValueError


class Profile(object):
    """
    An Orthography Profile as specified by Moran and Cysouw 2018.
    """
    GRAPHEME_COL = 'Grapheme'
    NULL = "NULL"
    MD = {
        "tables": [
            {
                "dialect": {
                    "delimiter": "\t",
                    "header": True,
                    "encoding": "utf-8"
                },
                "tableSchema": {
                    "columns": [
                        {
                            "name": GRAPHEME_COL,
                            "datatype": "string",
                            "required": True
                        }
                    ],
                    "primaryKey": GRAPHEME_COL
                }
            }
        ]
    }

    def __init__(self, *specs, **kw):
        """

        Parameters
        ----------
        specs : list of dict
            A list of grapheme specifications.
        kw :
            The following keyword arguments are recognized:
            - fname: Path of the profile or profile metadata.
            - form: Unicode normalization to apply to the data in the profile before use.
            - remaining keyword arguments are assigned as dict to `Profile.metadata`.
        """
        self.graphemes = OrderedDict()
        self.column_labels = set()
        self.fname = kw.pop('fname', None)
        self.form = kw.pop('form', None)
        self.metadata = kw

        log = logging.getLogger(__name__)
        for i, spec in enumerate(specs):
            if self.GRAPHEME_COL not in spec:
                raise ValueError('invalid grapheme specification')

            if self.form:
                spec = {
                    unicodedata.normalize(self.form, k):
                        None if v is None else unicodedata.normalize(self.form, v)
                    for k, v in spec.items()}

            grapheme = spec.pop(self.GRAPHEME_COL)
            if not grapheme:
                raise ValueError('Grapheme must not be empty')

            self.column_labels = self.column_labels.union(spec.keys())

            # check for duplicates in the orthography profile (fail if dups)
            if grapheme not in self.graphemes:
                self.graphemes[grapheme] = spec
            else:
                log.warning(
                    'line {0}:duplicate grapheme in profile: {1}'.format(i + 2, grapheme))
        self.tree = Tree(list(self.graphemes.keys()))

    def iteritems(self):
        for grapheme, spec in self.graphemes.items():
            res = {self.GRAPHEME_COL: grapheme}
            res.update({k: None for k in self.column_labels})
            res.update({k: v for k, v in spec.items()})
            yield res

    @classmethod
    def from_file(cls, fname, form=None):
        """
        Read an orthography profile from a metadata file or a default tab-separated profile file.
        """
        try:
            tg = TableGroup.from_file(fname)
            opfname = None
        except JSONDecodeError:
            tg = TableGroup.fromvalue(cls.MD)
            opfname = fname
        if len(tg.tables) != 1:
            raise ValueError('profile description must contain exactly one table')
        metadata = tg.common_props
        metadata.update(fname=Path(fname), form=form)
        return cls(
            *[{k: None if (k != cls.GRAPHEME_COL and v == cls.NULL) else v for k, v in d.items()}
              for d in tg.tables[0].iterdicts(fname=opfname)],
            **metadata)

    @classmethod
    def from_text(cls, text, mapping='mapping'):
        """
        Create a Profile instance from the Unicode graphemes found in `text`.

        Parameters
        ----------
        text
        mapping

        Returns
        -------
        A Profile instance.

        """
        graphemes = Counter(grapheme_pattern.findall(text))
        specs = [
            OrderedDict([
                (cls.GRAPHEME_COL, grapheme),
                ('frequency', frequency),
                (mapping, grapheme)])
            for grapheme, frequency in graphemes.most_common()]
        return cls(*specs)

    @classmethod
    def from_textfile(cls, fname, mapping='mapping'):
        return cls.from_text(' '.join(readlines(fname)), mapping=mapping)

    def __str__(self):
        """
        A Profile is represented as tab-separated lines of grapheme specifications.
        """
        tg = TableGroup.fromvalue(self.MD)
        for col in self.column_labels:
            if col != self.GRAPHEME_COL:
                tg.tables[0].tableSchema.columns.append(
                    Column.fromvalue({"name": col, "null": self.NULL}))

        return tg.tables[0].write(self.iteritems(), fname=None).decode('utf8').strip()
