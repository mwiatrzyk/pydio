#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# scripts/licenser/licenser.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------

import argparse
import fnmatch
import logging
import os
import re
import shutil
import sys
from datetime import datetime

logger = logging.getLogger(__name__)
this_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(this_dir, 'templates')
current_year = datetime.now().year


def render_template(name, **params):
    with open(os.path.join(template_dir, name)) as fd:
        return fd.read().format(**params)


def make_copyright_year(args):
    if args.released == current_year:
        return str(current_year)
    return "{} - {}".format(args.released, current_year)


def make_copyright_holder(args):
    return args.author


def update_license(args):
    copyright_year = make_copyright_year(args)
    copyright_holder = make_copyright_holder(args)
    license_text = render_template(
        'license.txt', year=copyright_year, holder=copyright_holder
    )
    license_file_path = os.path.join(args.project_root_dir, 'LICENSE.txt')
    license_file_path_old = license_file_path + '.old'
    shutil.move(license_file_path, license_file_path_old)
    with open(license_file_path, 'w') as fd:
        fd.write(license_text)
    os.unlink(license_file_path_old)


def update_source_files(args):

    def scan(path):
        for name in os.listdir(path):
            fullname = os.path.join(path, name)
            if os.path.isdir(fullname):
                yield from scan(fullname)
            else:
                yield fullname

    def is_match_found(path, patterns):
        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def include(paths, include_patterns):
        for path in paths:
            if is_match_found(path, include_patterns):
                yield path

    def exclude(paths, exclude_patterns):
        for path in paths:
            if not is_match_found(path, exclude_patterns):
                yield path

    def strip_project_root(path):
        return path.replace(args.project_root_dir + os.path.sep, '')

    def copy_stats(source_path, dest_path):
        stat = os.stat(source_path)
        os.chown(dest_path, stat.st_uid, stat.st_gid)
        os.chmod(dest_path, stat.st_mode)

    def leave_first_line(line):
        if line.startswith('#!'):  # shebang
            return True
        if re.match(
            r'-\*-\s+coding:.+\s+-\*-', line
        ):  # -*- coding: utf-8 -*- for example
            return True
        return False

    def update_path(path):
        _, file_ext = os.path.splitext(path)
        preamble = render_template(
            'preamble{}.txt'.format(file_ext),
            filename=strip_project_root(path),
            year=copyright_year,
            holder=copyright_holder
        )
        marker_line = preamble.split('\n')[0]
        path_old = path + '.old'
        shutil.move(path, path_old)
        try:
            with open(path, 'w') as dest:
                with open(path_old) as src:
                    line = src.readline()
                    if leave_first_line(line):
                        dest.write(line)
                        line = src.readline()
                    dest.write(preamble)
                    if line.startswith(marker_line):
                        line = src.readline()
                        while not line.startswith(marker_line):
                            line = src.readline()
                        line = src.readline()
                    while line:
                        dest.write(line)
                        line = src.readline()
        except Exception:
            shutil.move(path_old, path)  # restore file on error
            raise
        else:
            copy_stats(path_old, path)
            os.unlink(path_old)

    copyright_year = make_copyright_year(args)
    copyright_holder = make_copyright_holder(args)
    paths = scan(args.project_root_dir)
    if args.exclude:
        paths = exclude(paths, args.exclude)
    if args.include:
        paths = include(paths, args.include)
    for path in paths:
        logger.info('Updating path: %s', path)
        update_path(path)


def get_logging_level(args):
    if args.verbosity == 1:
        return logging.INFO
    if args.verbosity == 2:
        return logging.DEBUG
    return logging.WARNING


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='A tool for updating license and copyright notice in project'
    )
    parser.add_argument(
        'project_root_dir',
        metavar='PROJECT_ROOT_DIR',
        help='path to project root directory'
    )
    parser.add_argument(
        '--released',
        type=int,
        metavar='YEAR',
        required=True,
        help='year the project was first released'
    )
    parser.add_argument(
        '--author',
        type=str,
        metavar='NAME',
        required=True,
        help="author's name to be placed in license file and copyright notice"
    )
    parser.add_argument(
        '--include',
        '-i',
        action='append',
        metavar='PATTERN',
        help='add path pattern to include in processing'
    )
    parser.add_argument(
        '--exclude',
        '-e',
        action='append',
        metavar='PATTERN',
        help='add path pattern to exclude from processing'
    )
    parser.add_argument(
        '--verbosity', '-v', action='count', help='be more verbose'
    )
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    logging.basicConfig(
        level=get_logging_level(args),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    try:
        update_license(args)
        update_source_files(args)
    except Exception:  # pylint: disable=broad-except
        logger.error('An exception occured:', exc_info=True)
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
