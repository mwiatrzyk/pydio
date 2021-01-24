import pytest

from pydio.api import Injector, Provider

from tests.stubs import IDatabase, SQLiteDatabase, IAction, DummyAction

provider = Provider()
global_injector = Injector(provider)


@provider.provides('config')
def make_config(_):
    return {'env': 'testing'}


@provider.provides(IDatabase, scope='app')
def make_database(_):
    return SQLiteDatabase()


@provider.provides(IAction, scope='action')
def make_action(injector: Injector):
    return DummyAction(db=injector.inject(IDatabase))


class DummyApplication:

    def __init__(self):
        self._app_injector = global_injector.nested('app')

    def run(self):
        action_injector = self._app_injector.nested('action')
        with action_injector:
            return self.run_action(action_injector)

    def run_action(self, injector: Injector):
        return injector.inject(IAction)
