import pytest

from pydio.api import Provider, Injector

from tests.stubs import IDatabase, SQLiteDatabase, IAction, DummyAction

provider = Provider()


@provider.provides(IDatabase)
def make_database(*args):
    return SQLiteDatabase()


@provider.provides(IAction)
def make_action(injector: Injector, *args):
    return DummyAction(
        injector.inject(IDatabase))


@pytest.fixture
def injector():
    return Injector(provider)


def test_injector_should_inject_provided_instance_when_called(injector):
    obj = injector.inject(IDatabase)
    assert isinstance(obj, SQLiteDatabase)


def test_injector_should_always_inject_same_instance_each_time_it_is_called(injector):
    first = injector.inject(IDatabase)
    second = injector.inject(IDatabase)
    assert first is second


def test_two_distinct_injectors_will_inject_two_distinct_instances():
    assert Injector(provider).inject(IDatabase) is not Injector(provider).inject(IDatabase)


def test_provider_can_use_injector_for_nested_dependency_injections(injector):
    action = injector.inject(IAction)
    assert isinstance(action, DummyAction)
    assert isinstance(action.database, SQLiteDatabase)


def test_injector_should_raise_exception_if_no_provider_was_set_for_given_key(injector):
    with pytest.raises(Injector.NoProviderFound) as excinfo:
        injector.inject('dummy')
    assert str(excinfo.value) == "No provider found for key: 'dummy'"
