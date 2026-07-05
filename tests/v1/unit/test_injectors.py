import pytest

from mockify.api import Mock, Return, satisfied

from pydio.v1.injectors import Injector


@pytest.mark.skip
class TestInjector:
    @pytest.fixture
    def provider_mock(self):
        mock = Mock("provider_mock")
        with satisfied(mock):
            yield mock

    @pytest.fixture
    def constructor_mock(self):
        mock = Mock("constructor_mock")
        with satisfied(mock):
            yield mock

    @pytest.fixture
    def destructor_mock(self):
        mock = Mock("destructor_mock")
        with satisfied(mock):
            yield mock

    @pytest.fixture
    def env(self):
        return None

    @pytest.fixture
    def uut(self, provider_mock, env):
        return Injector(provider_mock, env=env)

    def test_injecting_object_for_the_first_time_creates_it(
        self, uut: Injector, provider_mock, constructor_mock, destructor_mock
    ):
        provider_mock.get_constructors.expect_call(int, env=None).will_once(Return((constructor_mock,)))
        constructor_mock.construct.expect_call().will_once(Return((123, destructor_mock)))
        value = uut.inject(int)
        assert value == 123

    @pytest.mark.parametrize("env", [None, "production"])
    def test_injecting_object_for_the_second_time_retrieves_previous_from_cache(
        self, uut: Injector, provider_mock, constructor_mock, destructor_mock, env
    ):
        provider_mock.get_constructors.expect_call(int, env=env).will_once(Return((constructor_mock,)))
        constructor_mock.construct.expect_call().will_once(Return((123, destructor_mock)))
        for _ in range(2):
            value = uut.inject(int)
            assert value == 123
