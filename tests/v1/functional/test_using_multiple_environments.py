import pytest

from mockify.api import Return

from pydio.v1.api import Provider, Injector, AsyncInjector, provides


@pytest.fixture
def provider(generic_mock):
    provider = Provider()

    @provides(provider, str)
    def make_default():
        return generic_mock.make_default()

    @provides(provider, str, env="testing")
    def make_testing():
        return generic_mock.make_testing()

    @provides(provider, str, env="production")
    def make_production():
        return generic_mock.make_production()

    return provider


class TestViaInjector:
    def test_inject_default(self, provider: Provider, generic_mock):
        injector = Injector(provider)
        generic_mock.make_default.expect_call().will_once(Return("spam"))
        assert injector.inject(str) == "spam"

    def test_inject_testing(self, provider: Provider, generic_mock):
        injector = Injector(provider, env="testing")
        generic_mock.make_testing.expect_call().will_once(Return("spam"))
        assert injector.inject(str) == "spam"

    def test_inject_production(self, provider: Provider, generic_mock):
        injector = Injector(provider, env="production")
        generic_mock.make_production.expect_call().will_once(Return("spam"))
        assert injector.inject(str) == "spam"

    def test_injecting_a_non_existing_environment_falls_back_to_default(self, provider: Provider, generic_mock):
        injector = Injector(provider, env="non-existing")
        generic_mock.make_default.expect_call().will_once(Return("spam"))
        assert injector.inject(str) == "spam"


class TestViaAsyncInjector:
    async def test_inject_default(self, provider: Provider, generic_mock):
        injector = AsyncInjector(provider)
        generic_mock.make_default.expect_call().will_once(Return("spam"))
        assert (await injector.inject(str)) == "spam"

    async def test_inject_testing(self, provider: Provider, generic_mock):
        injector = AsyncInjector(provider, env="testing")
        generic_mock.make_testing.expect_call().will_once(Return("spam"))
        assert (await injector.inject(str)) == "spam"

    async def test_inject_production(self, provider: Provider, generic_mock):
        injector = AsyncInjector(provider, env="production")
        generic_mock.make_production.expect_call().will_once(Return("spam"))
        assert (await injector.inject(str)) == "spam"

    async def test_injecting_a_non_existing_environment_falls_back_to_default(self, provider: Provider, generic_mock):
        injector = AsyncInjector(provider, env="non-existing")
        generic_mock.make_default.expect_call().will_once(Return("spam"))
        assert (await injector.inject(str)) == "spam"
