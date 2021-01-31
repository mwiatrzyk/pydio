import pytest

from mockify.mock import Mock
from mockify.actions import Return
from mockify.core import satisfied

from pydio.api import Injector, Provider

from tests.stubs import IFoo, Foo, IBar, Bar

provider = Provider()


@provider.provides('database')
def make_database(*args):
    return Mock('database')


@provider.provides(IFoo)
async def make_foo(*args):
    return Foo()


@provider.provides('connection')
def make_connection(injector: Injector, *args):
    db = injector.inject('database')
    connection = db.connect()
    yield connection
    connection.close()


@pytest.fixture
def injector():
    return Injector(provider)


@pytest.mark.asyncio
async def test_injector_should_properly_inject_coroutine_based_provider(injector):
    obj = await injector.inject(IFoo)
    assert isinstance(obj, Foo)


@pytest.mark.asyncio
async def test_when_async_injectors_present_then_injector_close_becomes_a_coroutine(injector):
    connection = Mock('connection')
    database = injector.inject('database')
    database.connect.expect_call().will_once(Return(connection))
    with satisfied(database):
        assert injector.inject('connection') is connection
    connection.close.expect_call().times(1)
    with satisfied(connection):
        await injector.close()
