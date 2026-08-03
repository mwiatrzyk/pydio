import pytest

from pydio.v1.providers import Provider
from pydio.v1.interface import ProviderLike, is_resource_factory, is_async_resource_factory
from pydio.v1.helpers import register_func, register_constant


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
