# ---------------------------------------------------------------------------
# tests/functional/conftest.py
#
# Copyright (C) 2021 - 2023 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import pytest
from mockify.core import assert_satisfied
from mockify.mock import Mock


@pytest.fixture
def mock():
    mock = Mock('mock')
    yield mock
    assert_satisfied(mock)
