import pytest

from pydio.api import Provider, Injector

from mockify.mock import Mock
from mockify.core import satisfied
from mockify.actions import Return

from tests.stubs import IFoo, Foo

provider = Provider()


@provider.provides('mock')
def make_mock(*args, **kwargs):
    return Mock('mock')


@provider.provides(IFoo)
def make_default_foo(injector: Injector, *args, **kwargs):
    return injector.inject('mock').make_default_foo(*args, **kwargs)


@provider.provides(IFoo, env='testing')
def make_testing_foo(injector: Injector, *args, **kwargs):
    return injector.inject('mock').make_testing_foo(*args, **kwargs)


@provider.provides(IFoo, env='production')
def make_production_foo(injector: Injector, *args, **kwargs):
    return injector.inject('mock').make_production_foo(*args, **kwargs)


@pytest.fixture
def default():
    return Injector(provider)


@pytest.fixture
def testing():
    return Injector(provider, env='testing')


@pytest.fixture
def production():
    return Injector(provider, env='production')


def test_default_injector_will_inject_using_default_factory(default):
    mock = default.inject('mock')
    mock.make_default_foo.expect_call(IFoo).will_once(Return(42))
    assert default.inject(IFoo) == 42


def test_testing_injector_will_inject_using_testing_factory(testing):
    mock = testing.inject('mock')
    mock.make_testing_foo.expect_call(IFoo, env='testing').will_once(Return(42))
    assert testing.inject(IFoo) == 42


def test_production_injector_will_inject_using_production_factory(production):
    mock = production.inject('mock')
    mock.make_production_foo.expect_call(IFoo, env='production').will_once(Return(42))
    assert production.inject(IFoo) == 42


def test_injector_with_non_existing_env_will_fall_back_to_default_factory():
    injector = Injector(provider, env='not_existing')
    mock = injector.inject('mock')
    mock.make_default_foo.expect_call(IFoo).will_once(Return(42))
    assert injector.inject(IFoo) == 42
