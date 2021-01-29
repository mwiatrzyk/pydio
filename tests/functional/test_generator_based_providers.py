import pytest

from mockify.mock import Mock
from mockify.core import satisfied
from mockify.actions import Return

from pydio.api import Provider, Injector

from tests.stubs import IDatabase, PostgresDatabase

provider = Provider()


@provider.provides('database')
def make_database(*args):
    return Mock('database')


@provider.provides(IDatabase)
def make_database_connection(injector: Injector, *args):
    db = injector.inject('database')
    connection = db.connect()
    yield connection
    connection.close()


@pytest.fixture
def injector():
    return Injector(provider)


@pytest.fixture
def connection(injector):
    connection = Mock('connection')
    database = injector.inject('database')
    database.connect.expect_call().will_once(Return(connection))
    with satisfied(database, connection):
        yield connection


def test_injector_should_inject_same_instances(injector, connection):
    first = injector.inject(IDatabase)
    second = injector.inject(IDatabase)
    assert first is second


def test_when_injector_is_closed_then_underlying_provider_is_closed_as_well(injector, connection):
    injector.inject(IDatabase)
    connection.close.expect_call().times(1)
    injector.close()
