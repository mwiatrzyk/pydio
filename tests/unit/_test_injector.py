import pytest

from mockify.mock import MockFactory, ABCMock
from mockify.actions import Return, Invoke
from mockify.core import satisfied, assert_satisfied

from pydio.api import Provider, Injector
from pydio.base import IProvider, IUnboundInstance, IInstance


@pytest.fixture
def provider_mock():
    provider = ABCMock('provider', IProvider)
    with satisfied(provider):
        yield provider


@pytest.fixture
def unbound_instance_mock():
    unbound_instance = ABCMock('unbound_instance', IUnboundInstance)
    with satisfied(unbound_instance):
        yield unbound_instance


@pytest.fixture
def instance_mock():
    instance = ABCMock('instance', IInstance)
    with satisfied(instance):
        yield instance


def test_when_inject_called_for_the_first_time_then_create_and_return_matching_object(provider_mock, unbound_instance_mock, instance_mock):
    uut = Injector(provider_mock)

    provider_mock.get.expect_call('foo').will_once(Return(unbound_instance_mock))
    unbound_instance_mock.bind.expect_call(uut).will_once(Return(instance_mock))
    instance_mock.get.expect_call().will_once(Return(42))

    assert uut.inject('foo') == 42


def test_when_injector_called_for_the_second_time_then_return_cached_object(provider_mock, unbound_instance_mock, instance_mock):
    uut = Injector(provider_mock)

    provider_mock.get.expect_call('foo').will_once(Return(unbound_instance_mock))
    unbound_instance_mock.bind.expect_call(uut).will_once(Return(instance_mock))
    instance_mock.get.expect_call().will_repeatedly(Return(42)).times(2)

    assert uut.inject('foo') == 42
    assert uut.inject('foo') == 42


def test_when_injector_is_closed_then_all_cached_objects_are_invalidated(provider_mock, unbound_instance_mock, instance_mock):
    uut = Injector(provider_mock)

    provider_mock.get.expect_call('foo').will_once(Return(unbound_instance_mock))
    unbound_instance_mock.bind.expect_call(uut).will_once(Return(instance_mock))
    instance_mock.get.expect_call().will_once(Return(42))

    assert uut.inject('foo') == 42

    instance_mock.invalidate.expect_call()

    uut.close()


def test_when_no_provider_found_then_raise_exception(provider_mock):
    uut = Injector(provider_mock)

    provider_mock.get.expect_call('foo').will_once(Return(None))

    with pytest.raises(Injector.NoProviderFound) as excinfo:
        uut.inject('foo')

    assert str(excinfo.value) == "No provider found for key: 'foo'"


def test_scoped_injector_looks_for_provider_with_same_scope(provider_mock, unbound_instance_mock, instance_mock):
    uut = Injector(provider_mock)

    app = uut.scoped('app')

    provider_mock.get.expect_call('foo', scope='app').will_once(Return(unbound_instance_mock))
    unbound_instance_mock.bind.expect_call(app).will_once(Return(instance_mock))
    instance_mock.get.expect_call().will_once(Return(42))

    assert app.inject('foo') == 42


def test_if_scoped_injector_cannot_find_provider_with_same_scope_then_it_asks_parent_injector(provider_mock, unbound_instance_mock, instance_mock):
    uut = Injector(provider_mock)

    app = uut.scoped('app')

    provider_mock.get.expect_call('foo', scope='app').will_once(Return(None))
    provider_mock.get.expect_call('foo').will_once(Return(unbound_instance_mock))
    unbound_instance_mock.bind.expect_call(uut).will_once(Return(instance_mock))
    instance_mock.get.expect_call().will_once(Return(42))

    assert app.inject('foo') == 42


def test_closing_parent_injector_automatically_cleans_up_scoped_injectors(provider_mock, unbound_instance_mock, instance_mock):
    uut = Injector(provider_mock)

    app = uut.scoped('app')

    provider_mock.get.expect_call('foo', scope='app').will_once(Return(unbound_instance_mock))
    unbound_instance_mock.bind.expect_call(app).will_once(Return(instance_mock))
    instance_mock.get.expect_call().will_once(Return(42))

    assert app.inject('foo') == 42

    instance_mock.invalidate.expect_call()

    uut.close()
