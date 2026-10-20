from __future__ import annotations

import pytest

from mockify.api import Return

from pydio.v1.providers import Provider
from pydio.v1.interface import (
    ProviderLike,
    SupportsInject,
    SupportsAsyncInject,
    is_resource_factory,
    is_async_resource_factory,
)
from pydio.v1.helpers import register_func, register_constant, provides


@pytest.fixture
def provider():
    return Provider()


class TestRegisterFunc:
    def test_register_function_and_require_it(self, provider: ProviderLike, scope, env, injector_stub):

        def make_object(injector):
            assert injector is injector_stub
            return 123

        register_func(provider, int, make_object, scope=scope, env=env)
        factory = provider.require_factory(int, scope=scope, env=env)
        assert is_resource_factory(factory, int)
        obj, _ = factory.create(injector_stub)
        assert obj == 123

    def test_register_generator_function_and_require_it(self, provider: ProviderLike, scope, env, injector_stub):

        def make_object(injector):
            assert injector is injector_stub
            yield 123

        register_func(provider, int, make_object, scope=scope, env=env)
        factory = provider.require_factory(int, scope=scope, env=env)
        assert is_resource_factory(factory, int)
        obj, _ = factory.create(injector_stub)
        assert obj == 123

    async def test_register_async_function_and_require_it(
        self, provider: ProviderLike, scope, env, async_injector_stub
    ):

        async def make_object(injector):
            assert injector is async_injector_stub
            return 123

        register_func(provider, int, make_object, scope=scope, env=env)
        factory = provider.require_factory(int, scope=scope, env=env)
        assert is_async_resource_factory(factory, int)
        obj, _ = await factory.create(async_injector_stub)
        assert obj == 123

    async def test_register_async_generator_function_and_require_it(
        self, provider: ProviderLike, scope, env, async_injector_stub
    ):

        async def make_object(injector):
            assert injector is async_injector_stub
            yield 123

        register_func(provider, int, make_object, scope=scope, env=env)
        factory = provider.require_factory(int, scope=scope, env=env)
        assert is_async_resource_factory(factory, int)
        obj, _ = await factory.create(async_injector_stub)
        assert obj == 123


class TestRegisterConstant:
    def test_register_constant_and_require_it(self, provider: ProviderLike, scope, env, injector_stub):
        register_constant(provider, int, 123, scope=scope, env=env)
        factory = provider.require_factory(int, scope=scope, env=env)
        assert is_resource_factory(factory)
        obj, _ = factory.create(injector_stub)
        assert obj == 123


class TestProvides:
    @pytest.fixture
    def provider(self):
        return Provider()

    class TestPassthroughMode:
        def test_pass_synchronous_injector(self, provider: Provider, injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env, mode="passthrough")
            def make_object(injector: SupportsInject | SupportsAsyncInject):
                return generic_mock(injector)

            factory = provider.require_factory(int, scope=scope, env=env)
            assert is_resource_factory(factory, int)
            generic_mock.expect_call(injector_stub).will_once(Return(123))
            obj, _ = factory.create(injector_stub)
            assert obj == 123

        def test_pass_async_injector(self, provider: Provider, async_injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env, mode="passthrough")
            def make_object(injector: SupportsInject | SupportsAsyncInject):
                return generic_mock(injector)

            factory = provider.require_factory(int, scope=scope, env=env)
            assert is_resource_factory(factory, int)
            generic_mock.expect_call(async_injector_stub).will_once(Return(123))
            obj, _ = factory.create(async_injector_stub)
            assert obj == 123

    class TestManualMode:
        def test_register_synchronous_factory(self, provider: Provider, injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env)
            def make_object(injector, typ, scope, env):
                return generic_mock(injector, typ, scope, env)

            factory = provider.require_factory(int, scope=scope, env=env)
            assert is_resource_factory(factory, int)
            generic_mock.expect_call(injector_stub, int, scope, env).will_once(Return(123))
            obj, _ = factory.create(injector_stub)
            assert obj == 123

        async def test_register_async_factory(self, provider: Provider, async_injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env)
            async def make_object(injector, typ, scope, env):
                return generic_mock(injector, typ, scope, env)

            factory = provider.require_factory(int, scope=scope, env=env)
            assert is_async_resource_factory(factory, int)
            generic_mock.expect_call(async_injector_stub, int, scope, env).will_once(Return(123))
            obj, _ = await factory.create(async_injector_stub)
            assert obj == 123

    class TestAutoMode:
        def test_register_synchronous_factory(self, provider: Provider, injector_stub, generic_mock, scope, env):

            @provides(provider, int, scope=scope, env=env, mode="auto")
            def make_object(foo: int, bar: float, baz: str):
                return generic_mock(foo, bar, baz)

            factory = provider.require_factory(int, scope=scope, env=env)
            assert is_resource_factory(factory, int)
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

            factory = provider.require_factory(int, scope=scope, env=env)
            assert is_async_resource_factory(factory, int)
            generic_mock.injector.inject.expect_call(int).will_once(Return(123))
            generic_mock.injector.inject.expect_call(float).will_once(Return(3.14))
            generic_mock.injector.inject.expect_call(str).will_once(Return("spam"))
            generic_mock.expect_call(123, 3.14, "spam").will_once(Return(123))
            obj, _ = await factory.create(async_injector_stub)
            assert obj == 123
