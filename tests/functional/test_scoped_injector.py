# ---------------------------------------------------------------------------
# tests/functional/test_scoped_injector.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import pytest
from mockify.actions import Return
from mockify.core import satisfied
from mockify.mock import Mock

from pydio.api import Injector, Provider
from tests.stubs import Bar, Baz, Foo, IBar, IFoo

provider = Provider()


@provider.provides('db')
def make_db():
    return Mock('db')


@provider.provides(IFoo)
def make_foo():
    return Foo()


@provider.provides(IBar, scope='sc1')
def make_bar():
    return Bar()


@provider.provides('connection', scope='sc1')
def make_connection(injector: Injector):
    db = injector.inject('db')
    connection = db.connect()
    yield connection
    connection.close()


@provider.provides('baz', scope='sc2')
def make_baz():
    return Baz()


@provider.provides('spam', scope='sc21')
def make_spam():
    return 'spam'


class TestScopedInjector:

    @pytest.fixture
    def injector(self):
        return Injector(provider)

    def test_root_injector_cannot_inject_scoped_providers(self, injector):
        assert isinstance(injector.inject(IFoo), Foo)
        with pytest.raises(Injector.OutOfScopeError) as excinfo:
            injector.inject(IBar)

    def test_scoped_injectors_should_inject_objects_with_matching_scope(
        self, injector
    ):
        sc1 = injector.scoped('sc1')
        sc2 = injector.scoped('sc2')
        assert isinstance(sc1.inject(IBar), Bar)
        assert isinstance(sc2.inject('baz'), Baz)

    def test_scoped_injector_falls_back_to_parent_if_it_cannot_find_provider_with_same_scope(
        self, injector
    ):
        sc1 = injector.scoped('sc1')
        assert isinstance(sc1.inject(IFoo), Foo)

    def test_scoped_injector_cannot_inject_objects_from_side_scope(
        self, injector
    ):
        sc1 = injector.scoped('sc1')
        with pytest.raises(Injector.OutOfScopeError):
            sc1.inject('baz')

    def test_scoped_injector_can_inject_objects_from_any_parent_scopes(
        self, injector
    ):
        sc2 = injector.scoped('sc2')
        sc21 = sc2.scoped('sc21')
        assert isinstance(sc21.inject(IFoo), Foo)
        assert isinstance(sc21.inject('baz'), Baz)
        assert sc21.inject('spam') == 'spam'

    def test_when_scoped_injector_is_closed_then_objects_it_created_are_cleared(
        self, injector
    ):
        sc1 = injector.scoped('sc1')

        connection = Mock('connection')
        db = injector.inject('db')
        db.connect.expect_call().will_once(Return(connection))
        with satisfied(db):
            assert sc1.inject('connection') is connection

        connection.close.expect_call().times(1)
        with satisfied(connection):
            sc1.close()

    def test_when_parent_injector_is_closed_then_child_injectors_are_closed_as_well(
        self, injector
    ):
        sc1 = injector.scoped('sc1')

        connection = Mock('connection')
        db = injector.inject('db')
        db.connect.expect_call().will_once(Return(connection))
        with satisfied(db):
            assert sc1.inject('connection') is connection

        connection.close.expect_call().times(1)
        with satisfied(connection):
            injector.close()
