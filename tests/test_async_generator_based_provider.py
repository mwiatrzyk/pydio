import pytest

from mockify.mock import Mock
from mockify.actions import Return
from mockify.core import satisfied

from pydio.api import Provider, Injector

provider = Provider()


@provider.provides('database')
def make_database(_, *args):
    return Mock('database')


@provider.provides('connection')
async def make_connection(injector: Injector, *args):
    database = injector.inject('database')
    connection = database.connect()
    yield connection
    connection.close()


@pytest.fixture
def injector():
    return Injector(provider)


@pytest.mark.asyncio
async def test_injector_should_properly_create_and_close_instances_provided_by_async_generators(injector):
    connection = Mock('connection')
    database = injector.inject('database')
    database.connect.expect_call().will_once(Return(connection))
    with satisfied(database):
        assert await injector.inject('connection') is connection
    connection.close.expect_call().times(1)
    with satisfied(connection):
        await injector.close()
