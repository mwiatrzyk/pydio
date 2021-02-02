import pytest

from mockify.mock import Mock
from mockify.core import satisfied
from mockify.actions import Return

from pydio.api import Injector, Provider

from tests.stubs import IFoo, Foo, IBar, Bar, Baz

provider = Provider()


@provider.provides('db')
def make_db(*args, **kwargs):
    return Mock('db')


@provider.provides(IFoo)
def make_foo(*args, **kwargs):
    return Foo()


@provider.provides(IBar, scope='sc1')
def make_bar(*args, **kwargs):
    return Bar()


@provider.provides('connection', scope='sc1')
def make_connection(injector: Injector, *args, **kwargs):
    db = injector.inject('db')
    connection = db.connect()
    yield connection
    connection.close()


@provider.provides('baz', scope='sc2')
def make_baz(*args, **kwargs):
    return Baz()


@provider.provides('spam', scope='sc21')
def make_spam(*args, **kwargs):
    return 'spam'


@pytest.fixture
def injector():
    return Injector(provider)


def test_root_injector_cannot_inject_scoped_providers(injector):
    assert isinstance(injector.inject(IFoo), Foo)
    with pytest.raises(Injector.OutOfScopeError) as excinfo:
        injector.inject(IBar)


def test_scoped_injectors_should_inject_objects_with_matching_scope(injector):
    sc1 = injector.scoped('sc1')
    sc2 = injector.scoped('sc2')
    assert isinstance(sc1.inject(IBar), Bar)
    assert isinstance(sc2.inject('baz'), Baz)


def test_scoped_injector_falls_back_to_parent_if_it_cannot_find_provider_with_same_scope(injector):
    sc1 = injector.scoped('sc1')
    assert isinstance(sc1.inject(IFoo), Foo)


def test_scoped_injector_cannot_inject_objects_from_side_scope(injector):
    sc1 = injector.scoped('sc1')
    with pytest.raises(Injector.OutOfScopeError):
        sc1.inject('baz')


def test_scoped_injector_can_inject_objects_from_any_parent_scopes(injector):
    sc2 = injector.scoped('sc2')
    sc21 = sc2.scoped('sc21')
    assert isinstance(sc21.inject(IFoo), Foo)
    assert isinstance(sc21.inject('baz'), Baz)
    assert sc21.inject('spam') == 'spam'


def test_when_scoped_injector_is_closed_then_objects_it_created_are_cleared(injector):
    sc1 = injector.scoped('sc1')

    connection = Mock('connection')
    db = injector.inject('db')
    db.connect.expect_call().will_once(Return(connection))
    with satisfied(db):
        assert sc1.inject('connection') is connection

    connection.close.expect_call().times(1)
    with satisfied(connection):
        sc1.close()


def test_when_parent_injector_is_closed_then_child_injectors_are_closed_as_well(injector):
    sc1 = injector.scoped('sc1')

    connection = Mock('connection')
    db = injector.inject('db')
    db.connect.expect_call().will_once(Return(connection))
    with satisfied(db):
        assert sc1.inject('connection') is connection

    connection.close.expect_call().times(1)
    with satisfied(connection):
        injector.close()
