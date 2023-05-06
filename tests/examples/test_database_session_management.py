# ---------------------------------------------------------------------------
# tests/examples/test_database_session_management.py
#
# Copyright (C) 2021 - 2023 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import abc

import pytest
from mockify.actions import Raise, Return
from mockify.core import ordered
from mockify.mock import Mock

from pydio.api import Injector, Provider
from pydio.injector import Injector
from pydio.provider import Provider


class ITodoItemStorage(abc.ABC):

    @abc.abstractmethod
    def create(self, data: dict) -> int:
        pass


class SQLTodoStorage(ITodoItemStorage):

    def __init__(self, session):
        self._session = session

    def create(self, data: dict) -> int:
        return self._session.insert(data)


provider = Provider()


@provider.provides('mock')
def make_mock():
    return Mock('mock')


@provider.provides('database')
def make_database(injector):
    mock = injector.inject('mock')
    return mock.database


@provider.provides('session', scope='action')
def create_connection(injector: Injector):
    database = injector.inject('database')
    with database.begin() as session:
        try:
            yield session
        except:
            session.rollback()
        else:
            session.commit()


@provider.provides(ITodoItemStorage, scope='action')
def make_sqlite_todo_storage(injector):
    return SQLTodoStorage(injector.inject('session'))


class Application:

    def __init__(self, injector):
        self._injector = injector

    def create(self, **params) -> int:
        with self._injector.scoped('action') as injector:
            storage: ITodoItemStorage = injector.inject(ITodoItemStorage)
            return storage.create(params)


@pytest.fixture
def injector():
    return Injector(provider)


@pytest.fixture
def mock(injector):
    return injector.inject('mock')


@pytest.fixture
def database(mock):
    return mock.database


@pytest.fixture
def session(mock):
    return mock.session


@pytest.fixture
def app(injector):
    with injector:
        yield Application(injector)


@pytest.fixture(
    params=[
        ValueError('a value error'),
        TypeError('a type error'),
        Exception('a generic error'),
    ]
)
def exc(request):
    return request.param


def test_expect_session_commit_when_action_is_executed_successfuly(
    app, database, session
):
    database.begin.expect_call().will_once(Return(session))
    session.insert.expect_call({'name': 'dummy'}).will_once(Return(123))
    session.commit.expect_call()
    with ordered(session):
        assert app.create(name='dummy') == 123


def test_expect_session_rollback_when_action_execution_fails_on_insert(
    app, database, session, exc
):
    with pytest.raises(exc.__class__) as excinfo:
        database.begin.expect_call().will_once(Return(session))
        session.insert.expect_call({'name': 'dummy'}).will_once(Raise(exc))
        session.rollback.expect_call()
        with ordered(session):
            app.create(name='dummy')
    assert excinfo.value is exc


def test_expect_session_commit_when_session_is_created_even_if_nothing_is_done_with_it(
    injector, database, session
):
    with injector.scoped('action') as injector:
        database.begin.expect_call().will_once(Return(session))
        session.commit.expect_call()
        assert isinstance(injector.inject(ITodoItemStorage), ITodoItemStorage)


def test_expect_session_rollback_when_session_is_created_and_exception_is_raised_just_after(
    injector, database, session, exc
):
    with pytest.raises(exc.__class__):
        with injector.scoped('action') as injector:
            database.begin.expect_call().will_once(Return(session))
            session.rollback.expect_call()
            assert isinstance(
                injector.inject(ITodoItemStorage), ITodoItemStorage
            )
            raise exc
