# ---------------------------------------------------------------------------
# tests/unit/test_injector.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
from pydio.injector import Injector


class TestInjectorErrors:

    def test_no_provider_found_error(self):
        uut = Injector.NoProviderFoundError(key='spam', env='testing')
        assert str(uut) == "No provider found for: key='spam', env='testing'"

    def test_out_of_scope_error(self):
        uut = Injector.OutOfScopeError(
            key='foo', scope='first', required_scope='second'
        )
        assert str(
            uut
        ) == "Cannot inject 'foo' due to scope mismatch: 'second' (required) != 'first' (owned)"
