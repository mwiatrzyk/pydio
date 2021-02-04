# ---------------------------------------------------------------------------
# tests/unit/test_base.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
from pydio.base import IInjector, IProvider


class TestIInjectorErrors:

    def test_no_provider_found_error(self):
        uut = IInjector.NoProviderFoundError(key='spam')
        assert str(uut) == "No provider found for key: 'spam'"

    def test_out_of_scope_error(self):
        uut = IInjector.OutOfScopeError(
            key='foo', expected_scope='sc1', given_scope='sc2'
        )
        assert str(
            uut
        ) == "Cannot inject 'foo' due to scope mismatch: 'sc1' (expected) != 'sc2' (given)"


class TestIProviderErrors:

    def test_double_registration_error(self):
        uut = IProvider.DoubleRegistrationError(key='foo', env='dummy')
        assert str(uut) == "Cannot register twice for: key='foo', env='dummy'"
