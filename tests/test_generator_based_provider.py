from typing import Hashable

import pytest

from mockify.mock import Mock
from mockify.core import satisfied

from pydio.api import Provider, Injector

from tests.stubs import IFoo, Foo

provider = Provider()


@provider.provides('startup')
@provider.provides('teardown')
def make_startup(_, key: Hashable):
    return Mock(key)


@provider.provides(IFoo)
def make_foo(injector: Injector, key: Hashable):
    startup = injector.inject('startup')
    teardown = injector.inject('teardown')
    startup()
    yield Foo()
    teardown()


@pytest.fixture
def injector():
    return Injector(provider)


def test_injector_should_inject_proper_object(injector):
    startup = injector.inject('startup')
    startup.expect_call().times(1)
    with satisfied(startup):
        assert isinstance(injector.inject(IFoo), Foo)


def test_injector_should_always_inject_same_instance(injector):
    startup = injector.inject('startup')
    startup.expect_call().times(1)
    with satisfied(startup):
        first = injector.inject(IFoo)
    second = injector.inject(IFoo)
    assert first is second


def test_when_injector_gets_closed_then_underlying_generator_proceeds_to_cleanup_phase(injector):
    test_injector_should_always_inject_same_instance(injector)
    teardown = injector.inject('teardown')
    teardown.expect_call().times(1)
    with satisfied(teardown):
        injector.close()


def test_use_injector_as_context_manager(injector):
    teardown = injector.inject('teardown')
    teardown.expect_call()
    with satisfied(teardown):
        with injector:
            startup = injector.inject('startup')
            startup.expect_call().times(1)
            with satisfied(startup):
                first = injector.inject(IFoo)
