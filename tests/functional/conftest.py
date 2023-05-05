import pytest

from mockify.core import assert_satisfied
from mockify.mock import Mock


@pytest.fixture
def mock():
    mock = Mock('mock')
    yield mock
    assert_satisfied(mock)
