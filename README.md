segments
========

[![Build Status](https://travis-ci.org/bambooforest/segments.svg?branch=master)](https://travis-ci.org/bambooforest/segments)
[![codecov](https://codecov.io/gh/bambooforest/segments/branch/master/graph/badge.svg)](https://codecov.io/gh/bambooforest/segments)
[![PyPI](https://img.shields.io/pypi/v/segments.svg)](https://pypi.python.org/pypi/segments)

The segments package provides Unicode Standard tokenization routines and orthography profile segmentation.


Command line usage
------------------

Create a text file:
```
$ more text.txt
aäaaöaaüaa
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

