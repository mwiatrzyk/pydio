from __future__ import annotations


import pytest

from mockify.api import Return

from pydio.v1.providers import Provider
from pydio.v1.decorators import provides
from pydio.v1.helpers import as_resource_factory, as_async_resource_factory
from pydio.v1.interface import SupportsInject, SupportsAsyncInject


@pytest.fixture
def provider():
    return Provider()


class TestProvides:
    class TestPassthroughMode:
        def test_pass_synchronous_injector(self, provider: Provider, injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env, mode="passthrough")
            def make_object(injector: SupportsInject | SupportsAsyncInject):
                return generic_mock(injector)

            factory = as_resource_factory(provider.require_factory(int, scope=scope, env=env))
            assert factory is not None
            generic_mock.expect_call(injector_stub).will_once(Return(123))
            obj, _ = factory.create(injector_stub)
            assert obj == 123

        def test_pass_async_injector(self, provider: Provider, async_injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env, mode="passthrough")
            def make_object(injector: SupportsInject | SupportsAsyncInject):
                return generic_mock(injector)

            factory = as_resource_factory(provider.require_factory(int, scope=scope, env=env))
            assert factory is not None
            generic_mock.expect_call(async_injector_stub).will_once(Return(123))
            obj, _ = factory.create(async_injector_stub)
            assert obj == 123

    class TestManualMode:
        def test_register_synchronous_factory(self, provider: Provider, injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env)
            def make_object(injector, typ, scope, env):
                return generic_mock(injector, typ, scope, env)

            factory = as_resource_factory(provider.require_factory(int, scope=scope, env=env))
            assert factory is not None
            generic_mock.expect_call(injector_stub, int, scope, env).will_once(Return(123))
            obj, _ = factory.create(injector_stub)
            assert obj == 123

        async def test_register_async_factory(self, provider: Provider, async_injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env)
            async def make_object(injector, typ, scope, env):
                return generic_mock(injector, typ, scope, env)

            factory = as_async_resource_factory(provider.require_factory(int, scope=scope, env=env))
            assert factory is not None
            generic_mock.expect_call(async_injector_stub, int, scope, env).will_once(Return(123))
            obj, _ = await factory.create(async_injector_stub)
            assert obj == 123

    class TestAutoMode:
        def test_register_synchronous_factory(self, provider: Provider, injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env, mode="auto")
            def make_object(foo: int, bar: float, baz: str):
                return generic_mock(foo, bar, baz)

            factory = as_resource_factory(provider.require_factory(int, scope=scope, env=env))
            assert factory is not None
            generic_mock.injector.inject.expect_call(int).will_once(Return(123))
            generic_mock.injector.inject.expect_call(float).will_once(Return(3.14))
            generic_mock.injector.inject.expect_call(str).will_once(Return("spam"))
            generic_mock.expect_call(123, 3.14, "spam").will_once(Return(123))
            obj, _ = factory.create(injector_stub)
            assert obj == 123

        async def test_register_async_factory(self, provider: Provider, async_injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env, mode="auto")
            async def make_object(foo: int, bar: float, baz: str):
                return generic_mock(foo, bar, baz)

            factory = as_async_resource_factory(provider.require_factory(int, scope=scope, env=env))
            assert factory is not None
            generic_mock.injector.inject.expect_call(int).will_once(Return(123))
            generic_mock.injector.inject.expect_call(float).will_once(Return(3.14))
            generic_mock.injector.inject.expect_call(str).will_once(Return("spam"))
            generic_mock.expect_call(123, 3.14, "spam").will_once(Return(123))
            obj, _ = await factory.create(async_injector_stub)
            assert obj == 123
