import pytest

from mockify.api import Mock, satisfied


@pytest.fixture
def generic_mock():
    mock = Mock("generic_mock")
    with satisfied(mock):
        yield mock
