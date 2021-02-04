# ---------------------------------------------------------------------------
# pydio/__init__.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
from pkg_resources import DistributionNotFound, get_distribution

__released__ = 2021
__author__ = 'Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>'
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = '0.1.0rc3'  # Use 'inv tag' to update this
