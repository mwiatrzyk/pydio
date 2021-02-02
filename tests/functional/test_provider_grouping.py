import pytest

from pydio.api import Provider, Injector

from tests.stubs import IFoo, Foo, IBar, Bar

foo_provider = Provider()
bar_provider = Provider()


@foo_provider.provides(IFoo)
def make_foo(*args, **kwargs):
    return Foo()


@bar_provider.provides(IBar)
def make_bar(*args, **kwargs):
    return Bar()


@pytest.fixture
def injector():
    provider = Provider()
    provider.attach(foo_provider)
    provider.attach(bar_provider)
    return Injector(provider)


def test_injector_should_inject_properly_when_provider_grouping_is_used(injector):
    assert isinstance(injector.inject(IFoo), Foo)
    assert isinstance(injector.inject(IBar), Bar)
