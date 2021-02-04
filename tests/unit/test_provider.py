# ---------------------------------------------------------------------------
# tests/unit/test_provider.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import pytest
from mockify.core import satisfied
from mockify.mock import ABCMock

from pydio.base import IInjector
from pydio.provider import Provider


class TestProvider:

    @pytest.fixture
    def uut(self):
        return Provider()

    @pytest.fixture
    def injector(self):
        mock = ABCMock('injector', IInjector)
        with satisfied(mock):
            yield mock

    def factory_function(self, key):
        return key

    def test_one_key_cannot_be_used_twice(self, uut):
        uut.register_func('foo', self.factory_function)
        with pytest.raises(Provider.DoubleRegistrationError) as excinfo:
            uut.register_func('foo', self.factory_function)
        assert excinfo.value.key == 'foo'

    def test_if_attached_provider_contains_duplicated_keys_it_will_be_rejected(
        self, uut
    ):
        other = Provider()
        other.register_func('foo', self.factory_function)
        uut.register_func('foo', self.factory_function)
        with pytest.raises(Provider.DoubleRegistrationError):
            uut.attach(other)

    def test_register_instance(self, uut, injector):
        uut.register_instance('foo', 123)
        unbound_factory = uut.get('foo')
        factory = unbound_factory.bind(injector)
        assert factory.get_instance() == 123

    def test_instance_cannot_be_registered_if_key_is_already_in_use(self, uut):
        uut.register_func('foo', self.factory_function)
        with pytest.raises(Provider.DoubleRegistrationError):
            uut.register_instance('foo', 123)
