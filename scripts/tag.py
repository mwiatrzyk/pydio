#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# scripts/tag.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------

import argparse
import contextlib
import glob
import itertools
import logging
import os
import re
import shutil
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s'
)

_THIS_DIR = os.path.abspath(os.path.dirname(__file__))
_ROOT_DIR = os.path.join(_THIS_DIR, '..')
_CHANGELOG_FILE_PATH = os.path.join(_ROOT_DIR, 'CHANGELOG.rst')
_SOURCES_PATH = os.path.join(_ROOT_DIR, 'pydio')
_DOCS_PATH = os.path.join(_ROOT_DIR, 'docs')
_INIT_FILE_PATH = os.path.join(_SOURCES_PATH, '__init__.py')
_NOW = datetime.now()
_TAG_RE = re.compile(r'^v?\d+\.\d+\.\d+(rc[0-9]+)?$')
_LIBRARY_VERSION_RE = re.compile(
    r"__version__\s+=\s+'(\d+\.\d+\.\d+(rc[0-9]+)?)'"
)
_CHANGELOG_TAG_RE = re.compile(
    r'(\(unreleased\))|((\d+\.\d+\.\d+(rc[0-9]+)?)\s+\((\d+-\d+-\d+)\))',
    flags=re.IGNORECASE
)
_SPHINX_ADDED_CHANGED_RE = re.compile(
    r'\.\. (versionadded|versionchanged|deprecated)\:\:\s+(\(unreleased\))',
    flags=re.IGNORECASE
)


@contextlib.contextmanager
def overwrite(path):

    def copy_stats(source_path, dest_path):
        stat = os.stat(source_path)
        os.chown(dest_path, stat.st_uid, stat.st_gid)
        os.chmod(dest_path, stat.st_mode)

    path_old = path + '.old'
    shutil.move(path, path_old)
    try:
        with open(path_old) as src:
            with open(path, 'w') as dest:
                yield src, dest
    except:
        shutil.move(path_old, path)  # restore backup on failure
        raise
    else:
        copy_stats(path_old, path)
        os.unlink(path_old)  # remove backup on success


def parse_version(args):
    version = args.tag_or_version
    if version.startswith('v'):
        return version[1:]
    return version


def update(args):

    def update_changelog(version):
        with overwrite(_CHANGELOG_FILE_PATH) as (src, dest):
            first_line = src.readline()
            if not _CHANGELOG_TAG_RE.match(first_line):
                raise ValueError(
                    'unexpected first line in {}: {}'.format(
                        _CHANGELOG_FILE_PATH, first_line
                    )
                )
            second_line = src.readline()
            if second_line.strip() != '-' * len(first_line.strip()):
                raise ValueError(
                    'invalid heading in {}:\n\n{}{}'.format(
                        _CHANGELOG_FILE_PATH, first_line, second_line
                    )
                )
            full_version_string = '{} ({})'.format(
                version, _NOW.strftime('%Y-%m-%d')
            )
            dest.write(full_version_string + '\n')
            dest.write('-' * len(full_version_string) + '\n')
            for line in src:
                dest.write(line)

    def update_init(version):
        with overwrite(_INIT_FILE_PATH) as (src, dest):
            for line in src:
                version_match = _LIBRARY_VERSION_RE.search(line)
                if version_match is not None:
                    line = line.replace(version_match.group(1), version)
                dest.write(line)

    def update_docstrings(version):
        major, minor, _ = version.split('.', 2)
        for path in itertools.chain(
            glob.glob(_SOURCES_PATH + '/**/*.py', recursive=True),
            glob.glob(_DOCS_PATH + '/**/*.rst', recursive=True)
        ):
            with overwrite(path) as (src, dest):
                for line in src:
                    found = _SPHINX_ADDED_CHANGED_RE.search(line)
                    if found is not None:
                        line = line.replace(
                            found.group(2), "{}.{}".format(major, minor)
                        )
                    dest.write(line)

    version_string = parse_version(args)
    update_changelog(version_string)
    update_init(version_string)
    update_docstrings(version_string)


def check(args):

    def split_version(version):
        if version == '(unreleased)':
            return version, _NOW
        match = _CHANGELOG_TAG_RE.search(version)
        return match.group(3), datetime.strptime(match.group(5), '%Y-%m-%d')

    def check_changelog(version):
        with open(_CHANGELOG_FILE_PATH) as fd:
            first_line = fd.readline().strip()
            second_line = fd.readline().strip()
            if second_line != '-' * len(first_line):
                raise ValueError(
                    'invalid heading in {}:\n\n{}\n{}\n'.format(
                        _CHANGELOG_FILE_PATH, first_line, second_line
                    )
                )
            last_version, last_date = split_version(first_line)
            if last_version != version:
                raise ValueError(
                    'unexpected version in {}: {} (found) != {} (expected)'.
                    format(_CHANGELOG_FILE_PATH, last_version, version)
                )
            if last_date > _NOW:
                raise ValueError(
                    'invalid date in {}: {} (date is in the future)'.format(
                        _CHANGELOG_FILE_PATH, last_date.strftime('%Y-%m-%d')
                    )
                )

    def check_init(version):
        with open(_INIT_FILE_PATH) as fd:
            for line in fd:
                found = _LIBRARY_VERSION_RE.search(line)
                if found is not None:
                    last_version = found.group(1)
                    if last_version != version:
                        raise ValueError(
                            'unexpected version in {}: {} (found) != {} (expected)'
                            .format(_INIT_FILE_PATH, last_version, version)
                        )

    def check_docstrings():
        for path in itertools.chain(
            glob.glob(_SOURCES_PATH + '/**/*.py', recursive=True),
            glob.glob(_DOCS_PATH + '/**/*.rst', recursive=True)
        ):
            with open(path) as fd:
                for line in fd:
                    found = _SPHINX_ADDED_CHANGED_RE.search(line)
                    if found is not None:
                        raise ValueError(
                            'unreleased mark present in file: {}'.format(path)
                        )

    version = parse_version(args)
    check_changelog(version)
    check_init(version)
    check_docstrings()


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='A tool for updating tag info in PyDio'
    )
    parser.add_argument(
        'tag_or_version',
        metavar='TAG_OR_VERSION',
        help='tag name or version string'
    )
    parser.add_argument(
        '-c',
        '--check-only',
        action='store_true',
        help=
        'instead of updating tag info, just check if it matches given tag or version'
    )
    args = parser.parse_args(argv)
    if not _TAG_RE.match(args.tag_or_version):
        parser.error('invalid TAG_OR_VERSION: {}'.format(args.tag_or_version))
    return args


def main(argv):
    args = parse_args(argv)
    try:
        if args.check_only:
            check(args)
        else:
            update(args)
    except Exception:  # pylint: disable=broad-except
        logger.error('An exception was raised:', exc_info=True)
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
