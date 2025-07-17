# -*- config:utf-8 -*-

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from codecs import open
from os import path
import re

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'unquotemail/__version__.py'), encoding='utf-8') as fp:
    try:
        version = re.findall(
            r"^__version__ = \"([^']+)\"\r?$", fp.read(), re.M
        )[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='unquotemail',
    version=version,
    license='MIT',
    description='Parse a given Html/Text email and return only the new text, without the quoted part.',
    long_description_content_type='text/markdown',
    long_description=long_description,
    url='https://github.com/getfernand/unquotemail',
    author='Cyril Nicodeme',
    author_email='contact@cnicodeme.com',
    keywords='mail email parse parser unquote reply eml',
    project_urls={
        # 'Official Website': 'https://github.com/getfernand/unquotemail',
        # 'Documentation': 'https://github.com/getfernand/unquotemail',
        'Source': 'https://github.com/getfernand/unquotemail',
    },
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4>=4.13.3',
        'Markdown>=3.7',
        'html2text>=2024.2.26',
    ],
    extras_require={
        'dev': ['pytest>=8.3.4'],
    },
    python_requires='>=3.3, <4',
    platforms='any',

    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',

        'Topic :: Communications :: Email',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Text Processing',

        "Operating System :: OS Independent",
        "Programming Language :: Python",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: PyPy",
    ]
)
