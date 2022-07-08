# Changelog

This project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [2.2.1] - 2022-07-08

- Fixed compatibility with csvw 3.x.
- Updated matrix of supported python versions.


## [2.2.0] - 2021-01-11

Fixed modifier combination in `ipa` mode.


## [2.1.3] - 2019-11-21

Fixed problems with edge cases in the IPA tokenization.


## [2.1.2] - 2019-11-07

Bugfix: See https://github.com/cldf/segments/issues/46


## [2.1.1] - 2019-11-05

Bugfix: Suppress csvw's UserWarning about unknown columns in orthography profiles
with more than the default columns.


## [2.1.0] - 2019-09-19

- Dropped py2 support
- Added compat for clldutils 3.x


## [2.0.1] - 2018-08-02

### Bug fixes

- Fixed a bug where NULL values in orthography profiles could not be read when
  the profile was initialized with Unicode normalization.


## [2.0.0] - 2018-08-01

### Added

`segments` now supports orthography profiles described by CSVW metadata.


### Backward Incompatibilities

Orthography profiles and the input of `Tokenizer.__call__` is no longer Unicode normalized
by default. I.e. the user is responsible for making sure profiles and tokenization
input are normalized correspondingly. Alternatively, profile data can be normalized
by passing a `form` keyword argument when initializing a `Profile` instance. But
also in this case, tokenization input must be normalized by the user.

While this results in a more cumbersome API, it gives the user in full control, e.g.
to avoid incorrect segmentation when parts of decomposed graphemes are appended to
preseding grapheme clusters. 
