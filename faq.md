
# Frequently asked questions

## How to treat word-initial or -final in a special way

Although it may seem a bit hacky, treating word-initial or -final graphemes differently is straightforward. We'll
use the common regular expression markers for start `^` and end `$`.

1. Create the orthography profile:

```python
>>> from segments.tokenizer import Profile
>>> prf = Profile(
 {'Grapheme': 'c', 'IPA': 'c'},
 {'Grapheme': '^', 'IPA': 'NULL'},
 {'Grapheme': '$', 'IPA': 'NULL'},
 {'Grapheme': 'a', 'IPA': 'b'},
 {'Grapheme': '^a', 'IPA': 'A'})
```

Note: We treat word-initial `a` differently!

2. Create the tokenizer

```python
>>> from segments.tokenizer import Tokenizer
>>> t = Tokenizer(prf)
>>> t('tha', 'IPA')
'tH b'
>>> t('ath', 'IPA')
'b tH'
>>> t('^ath', 'IPA')
'A tH'
```

3. Make sure to pass properly marked up words to the tokenizer:

```python
>>> t(' '.join('^' + s + '$' for s in 'tha ath'.split()), 'IPA')
'tH b # A tH'
```
