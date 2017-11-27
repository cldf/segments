# Contributing

While you can contribute to `segments` by opening issues when you encounter bugs
or would like to see new functionality, we also encourage you to submit 
pull requests, following the [standard fork & pr workflow](https://gist.github.com/Chaser324/ce0505fbed06b947d962).

To be able to create meaningful pull requests, you must install `segments` in
development mode, i.e. after cloning your fork of the repository,
- create a new [virtual environment](https://docs.python.org/3/tutorial/venv.html)
- activate the virtual env
- install `segments` and all dependencies required for development:
```
pip install -e .[dev,test]
```

Now you should be able to 
- edit the code in `src/segments`,
- add tests in `tests/`,
- make sure the test suite still passes running `pytest`,
- make sure your changes adhere to the coding standards running `flake8`.
