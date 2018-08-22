segments
========

[![Build Status](https://travis-ci.org/cldf/segments.svg?branch=master)](https://travis-ci.org/cldf/segments)
[![codecov](https://codecov.io/gh/cldf/segments/branch/master/graph/badge.svg)](https://codecov.io/gh/cldf/segments)
[![PyPI](https://img.shields.io/pypi/v/segments.svg)](https://pypi.org/project/segments)


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1051158.svg)](https://doi.org/10.5281/zenodo.1051158)

The segments package provides Unicode Standard tokenization routines and orthography profile segmentation.


Command line usage
------------------

Create a text file:
```
$ echo "aäaaöaaüaa" > text.txt
```

Now look at the profile:
```
$ cat text.txt | segments profile
Grapheme        frequency       mapping
a       7       a
ä       1       ä
ü       1       ü
ö       1       ö
```

Write the profile to a file:
```
$ cat text.txt | segments profile > profile.prf
```

Edit the profile:

```
$ more profile.prf
Grapheme        frequency       mapping
aa      0       x
a       7       a
ä       1       ä
ü       1       ü
ö       1       ö
```

Now tokenize the text without profile:
```
$ cat text.txt | segments tokenize
a ä a a ö a a ü a a
```

And with profile:
```
$ cat text.txt | segments --profile=profile.prf tokenize
a ä aa ö aa ü aa

$ cat text.txt | segments --mapping=mapping --profile=profile.prf tokenize
a ä x ö x ü x
```


API
---

```python
>>> from __future__ import unicode_literals, print_function
>>> from segments import Profile, Tokenizer
>>> t = Tokenizer()
>>> t('abcd')
'a b c d'
>>> prf = Profile({'Grapheme': 'ab', 'mapping': 'x'}, {'Grapheme': 'cd', 'mapping': 'y'})
>>> print(prf)
Grapheme	mapping
ab	x
cd	y
>>> t = Tokenizer(profile=prf)
>>> t('abcd')
'ab cd'
>>> t('abcd', column='mapping')
'x y'
```
