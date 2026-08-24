from __future__ import annotations

import pytest

from pydio.v1.exc import FactoryAlreadyExistsError, FactoryNotFoundError, OutOfScopeError
from pydio.v1.helpers import register_func, register_constant
from pydio.v1.providers import Provider
from pydio.v1.interface import is_resource_factory


class TestProvider:
    UUT = Provider

    @pytest.fixture
    def uut(self):
        return Provider()

    def test_registering_same_type_twice_causes_error(self, uut: UUT, scope, env):

        def make_object(injector):
            return 123

        register_func(uut, int, make_object, scope=scope, env=env)
        with pytest.raises(FactoryAlreadyExistsError):
            register_func(uut, int, make_object, scope=scope, env=env)

    def test_registering_an_unsupported_object_as_factory_causes_error(self, uut: UUT):
        func = object()
        with pytest.raises(TypeError) as excinfo:
            register_func(uut, int, func)
        assert str(excinfo.value) == f"Cannot use non-callable object {func!r} as a resource factory"

    def test_require_factory_fails_if_type_is_missing(self, uut: UUT, scope, env):
        with pytest.raises(FactoryNotFoundError) as excinfo:
            uut.require_factory(int, scope=scope, env=env)
        assert str(excinfo.value) == f"No factory found for query: typ={int!r}, scope={scope!r}, env={env!r}"

    @pytest.mark.parametrize(
        "registered_scopes, required_scope",
        [
            [[("b",)], ("a",)],
            [[("a", "b")], ("a",)],
            [[("a", "b")], ("a", "c")],
            [[("a", "b")], tuple()],
            [[("a", "b"), ("a", "b", "c"), ("b",), ("b", "c", "d", "e"), ("f",)], tuple()],
            [
                [("a", "b"), ("a", "b", "c"), ("b",), ("b", "c", "d", "e"), ("f",)],
                ("c", "d", "e"),
            ],
        ],
    )
    def test_require_factory_fails_if_type_is_located_under_unrelated_scope(
        self, uut: UUT, registered_scopes, required_scope, env
    ):
        for i, registered_scope in enumerate(registered_scopes):
            register_func(uut, int, lambda: i, scope=registered_scope, env=env)
        with pytest.raises(OutOfScopeError) as excinfo:
            uut.require_factory(int, scope=required_scope, env=env)
        assert excinfo.value.typ == int
        assert excinfo.value.scope == required_scope
        assert excinfo.value.env == env
        assert excinfo.value.existing_scopes == registered_scopes

    def test_require_factory_fails_if_type_is_located_under_different_env_and_also_default_env_is_missing(
        self, uut: UUT
    ):
        register_constant(uut, int, 123, env="production")
        with pytest.raises(FactoryNotFoundError) as excinfo:
            uut.require_factory(int, env="testing")
        assert excinfo.value.typ == int
        assert excinfo.value.scope == ()
        assert excinfo.value.env == "testing"

    def test_require_factory_falls_back_to_default_env(self, uut: UUT, injector_stub):
        register_constant(uut, int, 123)
        factory = uut.require_factory(int, env="testing")
        assert is_resource_factory(factory, int)
        obj, _ = factory.create(injector_stub)
        assert obj == 123

    def test_register_factory_for_different_scopes_and_then_return_the_one_with_best_match(
        self, uut: UUT, injector_stub
    ):
        register_func(uut, int, lambda: 1)
        register_func(uut, int, lambda: 2, scope=("a",))
        register_func(uut, int, lambda: 3, scope=("a", "b"))
        first = uut.require_factory(int, scope=("a", "b", "c"))
        assert is_resource_factory(first, int)
        obj, _ = first.create(injector_stub)
        assert obj == 3
        second = uut.require_factory(int, scope=("a", "d"))
        assert is_resource_factory(second, int)
        obj, _ = second.create(injector_stub)
        assert obj == 2
        third = uut.require_factory(int, scope=("b",))
        assert is_resource_factory(third, int)
        obj, _ = third.create(injector_stub)
        assert obj == 1

    def test_when_another_provider_attached_then_lookup_recurses_into_it(self, uut: UUT, injector_stub, scope, env):
        child = Provider()
        register_func(child, int, lambda: 123, scope=scope, env=env)
        uut.attach(child)
        factory = uut.require_factory(int, scope=scope, env=env)
        assert is_resource_factory(factory, int)
        obj, _ = factory.create(injector_stub)
        assert obj == 123

    def test_when_two_providers_attached_and_found_in_second_then_return_that_factory(self, uut: UUT):
        one = Provider()
        two = Provider()
        register_func(two, int, lambda: 123)
        uut.attach(one)
        uut.attach(two)
        factory = uut.require_factory(int)
        assert is_resource_factory(factory)

    def test_when_double_nested_providers_attached_then_found_in_grandchild(self, uut: UUT):
        grandchild = Provider()
        register_func(grandchild, int, lambda: 123)
        child = Provider()
        child.attach(grandchild)
        uut.attach(child)
        factory = uut.require_factory(int)
        assert is_resource_factory(factory, int)

    def test_when_registered_in_current_then_skip_recursing_into_nested(self, uut: UUT, injector_stub):
        grandchild = Provider()
        register_func(grandchild, int, lambda: 123)
        child = Provider()
        child.attach(grandchild)
        uut.attach(child)
        register_func(uut, int, lambda: 456)
        factory = uut.require_factory(int)
        assert is_resource_factory(factory, int)
        obj, _ = factory.create(injector_stub)
        assert obj == 456

    def test_when_not_registered_anywhere_then_raise_error(self, uut: UUT, injector_stub):
        grandchild = Provider()
        register_func(grandchild, int, lambda: 123)
        child = Provider()
        child.attach(grandchild)
        uut.attach(child)
        register_func(uut, int, lambda: 456)
        with pytest.raises(FactoryNotFoundError):
            uut.require_factory(float)

    def test_when_nested_raises_out_of_scope_then_it_propagates(self, uut: UUT, env):
        child = Provider()
        register_func(child, int, lambda: 123, scope=("bar",), env=env)
        uut.attach(child)
        with pytest.raises(OutOfScopeError) as excinfo:
            uut.require_factory(int, scope=("foo",), env=env)
        assert excinfo.value.typ == int
        assert excinfo.value.scope == ("foo",)
        assert excinfo.value.env == env
