
Releasing segments
==================

- Do platform test via tox:
```
tox -r
```

- Make sure flake8 passes:
```
flake8
```

- Change version to the new version number in

  - `setup.py`
  - `src/segments/__init__.py`

- Bump version number:
```
git commit -a -m"bumped version number"
```

- Create a release tag:
```
git tag -a v<version> -m"first version to be released on pypi"
```

- Push to github:
```
git push origin
git push --tags
```

- Make sure your system Python has ``setuptools-git`` installed and release to PyPI:
```
git checkout tags/v$1
python setup.py sdist
python setup.py bdist_wheel
twine upload dist/*
```
