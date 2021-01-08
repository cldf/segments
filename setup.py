from setuptools import setup, find_packages


setup(
    name='segments',
    version="2.2.0",
    description='',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author='Steven Moran and Robert Forkel',
    author_email='steven.moran@uzh.ch',
    url='https://github.com/cldf/segments',
    install_requires=[
        'regex',
        'csvw>=1.5.6',
        'clldutils>=1.7.3',
    ],
    extras_require={
        'dev': ['flake8', 'wheel', 'twine'],
        'test': [
            'pytest>=5',
            'pytest-mock',
            'pytest-cov',
        ],
    },
    license='Apache 2.0',
    zip_safe=False,
    keywords='tokenizer',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            "segments = segments.__main__:main",
        ]
    },
)
