import pytest

from pydio.api import Provider, Injector

from tests.stubs import IDatabase, SQLiteDatabase, IAction, DummyAction

provider = Provider()


@provider.provides(IDatabase)
async def make_database(*args):
    return SQLiteDatabase()


@provider.provides(IAction)
async def make_action(injector: Injector, *args):
    return DummyAction(
        await injector.inject(IDatabase))


@pytest.fixture
def injector():
    return Injector(provider)


@pytest.mark.asyncio
async def test_inject_action_asynchronously(injector):
    action = await injector.inject(IAction)
    assert isinstance(action, DummyAction)
    assert isinstance(action.database, SQLiteDatabase)


@pytest.mark.asyncio
async def test_inject_should_always_inject_same_object_in_async_mode(injector):
    first = await injector.inject(IDatabase)
    second = await injector.inject(IDatabase)
    assert first is second
