
Releasing segments
==================

- Do platform test via tox:
  ```shell
  tox -r
  ```

- Make sure flake8 passes:
  ```shell
  flake8 src
  ```

- Update the version number, by removing the trailing `.dev0` in:
  - `setup.cfg`
  - `src/segments/__init__.py`

- Update `CHANGES.md`

- Create the release commit:
  ```shell
  git commit -a -m "release <VERSION>"
  ```

- Create a release tag:
  ```
  git tag -a v<VERSION> -m"<VERSION> release"
  ```

- Release to PyPI:
  ```shell
  python setup.py clean --all
  rm dist/*
  python -m build -n
  twine upload dist/*
  ```

- Push to github:
  ```shell
  git push origin
  git push --tags
  ```

- Increment version number and append `.dev0` to the version number for the new development cycle:
  - `src/segments/__init__.py`
  - `setup.cfg`

- Commit/push the version change:
  ```shell
  git commit -a -m "bump version for development"
  git push origin
  ```
