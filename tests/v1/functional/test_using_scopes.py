import pytest

from mockify.api import Return

from pydio.v1.api import Provider, Injector, AsyncInjector, OutOfScopeError, provides

from tests.v1.functional.types import UserType, HostType, PortType, Config


@pytest.fixture
def provider(generic_mock):
    provider = Provider()

    @provides(provider, UserType)
    def make_user():
        return generic_mock.make_user()

    @provides(provider, HostType, scope=("foo",))
    def make_host():
        return generic_mock.make_host()

    @provides(provider, PortType, scope=("foo",))
    def make_port():
        return generic_mock.make_port()

    @provides(provider, Config, scope=("foo", "bar"), mode="auto", env="sync")
    def make_scope_sync(user: UserType, host: HostType, port: PortType):
        return Config(user, host, port)

    @provides(provider, Config, scope=("foo", "bar"), mode="auto", env="async")
    async def make_scope_async(user: UserType, host: HostType, port: PortType):
        return Config(user, host, port)

    return provider


class TestWithInjector:
    @pytest.fixture
    def injector(self, provider: Provider):
        return Injector(provider, env="sync")

    def test_out_of_scope_is_raised_if_config_is_tried_to_be_injected_from_root_scope(self, injector: Injector):
        with pytest.raises(OutOfScopeError):
            injector.inject(Config)

    def test_inject_after_creating_required_scope(self, injector: Injector, generic_mock):
        with injector.scoped("foo") as foo:
            with foo.scoped("bar") as bar:
                generic_mock.make_user.expect_call().will_once(Return("root"))
                generic_mock.make_host.expect_call().will_once(Return("localhost"))
                generic_mock.make_port.expect_call().will_once(Return(1234))
                assert bar.inject(Config) == Config("root", "localhost", 1234)


class TestWithAsyncInjector:
    @pytest.fixture
    def injector(self, provider: Provider):
        return AsyncInjector(provider, env="async")

    async def test_out_of_scope_is_raised_if_config_is_tried_to_be_injected_from_root_scope(
        self, injector: AsyncInjector
    ):
        with pytest.raises(OutOfScopeError):
            await injector.inject(Config)

    async def test_inject_after_creating_required_scope(self, injector: AsyncInjector, generic_mock):
        async with injector.scoped("foo") as foo:
            async with foo.scoped("bar") as bar:
                generic_mock.make_user.expect_call().will_once(Return("root"))
                generic_mock.make_host.expect_call().will_once(Return("localhost"))
                generic_mock.make_port.expect_call().will_once(Return(1234))
                assert (await bar.inject(Config)) == Config("root", "localhost", 1234)
