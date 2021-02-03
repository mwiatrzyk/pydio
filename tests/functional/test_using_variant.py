# ---------------------------------------------------------------------------
# tests/functional/test_using_variant.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import pytest
from mockify.actions import Return
from mockify.core import satisfied
from mockify.mock import Mock

from pydio.api import Injector, Provider, Variant
from tests.stubs import IFoo

IFoo1 = Variant(IFoo, 1, 2, c='one')

IFoo2 = Variant(IFoo, 1, 2, c='two')

provider = Provider()


@provider.provides('mock')
def make_mock(*args, **kwargs):
    return Mock('mock')


@provider.provides(IFoo1)
@provider.provides(IFoo2)
def make_first_foo(injector: Injector, key: Variant, *args, **kwargs):
    return injector.inject('mock').make_first_foo(key)


@pytest.fixture
def injector():
    return Injector(provider)


def test_inject_using_variant_to_pass_additional_params_to_underlying_factory(
    injector
):
    mock = injector.inject('mock')
    mock.make_first_foo.expect_call(IFoo1).will_once(Return('first'))
    mock.make_first_foo.expect_call(IFoo2).will_once(Return('second'))
    with satisfied(mock):
        assert injector.inject(IFoo1) == 'first'
        assert injector.inject(IFoo2) == 'second'
