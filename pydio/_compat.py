# ---------------------------------------------------------------------------
# pydio/_compat.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import sys

_py_version = (sys.version_info.major, sys.version_info.minor)

if _py_version >= (3, 7):

    from contextlib import AbstractAsyncContextManager

else:  # Py36

    import abc

    class AbstractAsyncContextManager(abc.ABC):

        async def __aenter__(self):
            return self

        @abc.abstractmethod
        async def __aexit__(self, exc_type, exc, tb):
            pass
