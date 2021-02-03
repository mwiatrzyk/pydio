# ---------------------------------------------------------------------------
# setup.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import setuptools


with open("README.rst", "r") as fd:
    long_description = fd.read()


setuptools.setup(
    name="PyDio",
    use_scm_version={
        'write_to': 'pydio/_version.py',
    },
    setup_requires=['setuptools_scm'],
    author="Maciej Wiatrzyk",
    author_email="maciej.wiatrzyk@gmail.com",
    description="A simple and powerful dependency injection toolkit for Python",
    long_description=long_description,
    #long_description_content_type="text/markdown",
    url="https://pydio.readthedocs.io/",
    packages=setuptools.find_packages(exclude=["docs", "tests*"]),
    keywords="dependency, injection, di, framework, toolkit, tool, library",
    python_requires=">=3.6, <4",
    project_urls={
        'Bug Reports': "https://gitlab.com/zef1r/pydio/-/issues",
        'Source': "https://gitlab.com/zef1r/pydio",
        'Documentation': "https://pydio.readthedocs.io/",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        #"Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        #"Topic :: Software Development :: Libraries",
    ],
)
