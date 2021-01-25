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


class BaseTest:

    def setup_method(self):
        self.provider = Provider()
        self.injector = Injector(self.provider)
        self.mock_factory = MockFactory()

    def teardown_method(self):
        assert_satisfied(self.mock_factory)


class TestBasics(BaseTest):

    def make_object(self, *args, **kwargs):
        return object()

    def test_inject_should_return_object_created_by_provided_factory_function(self):
        make_foo = self.mock_factory.mock('make_foo')
        make_foo.expect_call(self.injector).will_once(Return(42))

        self.provider.register_func('foo', make_foo)

        obj = self.injector.inject('foo')
        assert obj == 42

    def test_inject_should_call_factory_function_only_once_and_return_same_object_every_time(self):
        make_foo = self.mock_factory.mock('make_foo')
        make_foo.expect_call(self.injector).will_once(Invoke(self.make_object))

        self.provider.register_func('foo', make_foo)

        first = self.injector.inject('foo')
        second = self.injector.inject('foo')
        assert first is second

    def test_if_two_injectors_created_then_each_calls_factory_function(self):
        other_injector = Injector(self.provider)

        make_foo = self.mock_factory.mock('make_foo')
        make_foo.expect_call(self.injector).will_once(Invoke(self.make_object))
        make_foo.expect_call(other_injector).will_once(Invoke(self.make_object))

        self.provider.register_func('foo', make_foo)

        assert self.injector.inject('foo') is not other_injector.inject('foo')

    def test_during_creation_of_object_injector_can_be_used_to_create_nested_dependencies(self):
        make_bar = self.mock_factory.mock('make_bar')
        make_bar.expect_call(self.injector).will_once(Return(42))

        def make_foo(injector):
            return injector.inject('bar')

        self.provider.register_func('foo', make_foo)
        self.provider.register_func('bar', make_bar)

        assert self.injector.inject('foo') is 42

    def test_if_no_provider_found_for_given_key__then_raise_exception_on_inject(self):
        with pytest.raises(Injector.NoProviderFound) as excinfo:
            self.injector.inject('foo')
        assert str(excinfo.value) == "No provider found for key: 'foo'"


class TestGeneratorBasedFactory(BaseTest):

    def setup_method(self):
        super().setup_method()
        self.before = self.mock_factory.mock('before')
        self.after = self.mock_factory.mock('after')
        self.provider.register_func('foo', self.make_foo)

    def make_foo(self, *args, **kwargs):
        self.before(*args, **kwargs)
        yield object()
        self.after()

    def test_inject_will_always_inject_same_object(self):
        self.before.expect_call(self.injector)

        first = self.injector.inject('foo')
        second = self.injector.inject('foo')
        assert first is second

    def test_two_injectors_will_inject_two_different_objects(self):
        other_injector = Injector(self.provider)

        self.before.expect_call(self.injector)
        self.before.expect_call(other_injector)

        first = self.injector.inject('foo')
        second = other_injector.inject('foo')
        assert first is not second

    def test_when_injector_is_closed_then_cleanup_actions_are_invoked(self):
        self.before.expect_call(self.injector)

        self.injector.inject('foo')

        self.after.expect_call()

        self.injector.close()

    def test_close_injector_just_after_it_is_created(self):
        self.injector.close()
