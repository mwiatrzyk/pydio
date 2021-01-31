import pytest

from mockify.mock import Mock
from mockify.actions import Return
from mockify.core import satisfied

from pydio import exc, base, _factory as factory


class TestGeneratorFactory:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.uut = factory.GeneratorFactory(self.make_connection)
        self.database = Mock('database')

    def make_connection(self):
        connection = self.database.connect()
        yield connection
        connection.close()

    def get_instance_and_then_close(self):
        connection = Mock('connection')
        self.database.connect.expect_call().will_once(Return(connection))
        with satisfied(self.database):
            assert self.uut.get_instance() is connection
        connection.close.expect_call().times(1)
        with satisfied(connection):
            self.uut.close()

    def test_generator_factory_is_not_awaitable(self):
        assert not self.uut.is_awaitable()

    def test_get_instance_always_returns_same_object(self):
        connection = Mock('connection')
        self.database.connect.expect_call().will_once(Return(connection))
        with satisfied(self.database):
            assert self.uut.get_instance() is connection
            assert self.uut.get_instance() is connection

    def test_closing_generator_factory_invokes_statement_after_yield(self):
        self.get_instance_and_then_close()

    def test_closing_generator_factory_again_has_no_effect(self):
        self.get_instance_and_then_close()
        self.uut.close()

    def test_get_instance_returns_null_if_called_after_close(self):
        self.uut.close()
        assert self.uut.get_instance() is base.NULL
