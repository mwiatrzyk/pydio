import pytest

from pydio.provider import Provider


@pytest.fixture
def uut():
    return Provider()


def factory_function(_, key):
    return key


def test_one_key_cannot_be_used_twice(uut):
    uut.register_func('foo', factory_function)
    with pytest.raises(Provider.DoubleRegistrationError) as excinfo:
        uut.register_func('foo', factory_function)
    assert excinfo.value.key == 'foo'
