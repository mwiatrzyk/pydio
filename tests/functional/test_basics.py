from typing import Hashable

import pytest

from pydio.api import Provider, Injector

from tests.stubs import IFoo, IBar, Foo, Bar, Baz

provider = Provider()


@provider.provides(IFoo)
def make_foo(*args):
    return Foo()


@provider.provides(IBar)
def make_bar(*args):
    return Bar()


@provider.provides('baz')
def make_baz(injector: Injector, key: Hashable):
    return Baz(
        foo=injector.inject(IFoo),
        bar=injector.inject(IBar))


@pytest.fixture
def injector():
    return Injector(provider)


def test_injector_should_inject_expected_object(injector):
    assert isinstance(injector.inject(IFoo), Foo)


def test_injector_should_always_inject_same_instance(injector):
    assert injector.inject(IFoo) is injector.inject(IFoo)


def test_injector_should_raise_exception_if_invalid_key_was_given(injector):
    with pytest.raises(Injector.NoProviderFoundError) as excinfo:
        injector.inject('dummy')
    assert excinfo.value.key == 'dummy'


def test_injector_can_perform_nested_injections_if_needed(injector):
    baz = injector.inject('baz')
    assert isinstance(baz, Baz)
    assert isinstance(baz.foo, Foo)
    assert isinstance(baz.bar, Bar)


def test_injector_can_no_longer_be_used_after_close(injector):
    injector.close()
    with pytest.raises(Injector.AlreadyClosedError):
        injector.inject(IFoo)
