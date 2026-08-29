from __future__ import annotations

import io
import textwrap
import traceback
from typing import Callable

import pytest

from pydio.v1 import _factories
from pydio.v1.exc import (
    IncompleteClosingError,
    InjectorAlreadyClosedError,
    OutOfScopeError,
    ResourceFactoryAlreadyExistsError,
    ResourceFactoryNotFoundError,
    IncompatibleResourceFactoryFoundError,
    ScopedInjectorAlreadyExistsError,
    UserFactoryDeclarationError,
    UserFactoryPreconditionError,
)
from pydio.v1.injectors import Injector
from pydio.v1.interface import ScopeType
from pydio.v1.providers import Provider

provider = Provider()
injector = Injector(provider)


def foo(a: int, b: str, c: float, d: bool):
    pass


def bar(a: int, b: str, c, d):
    pass


def baz(injector):
    pass


def format_name(func: Callable):
    return func.__name__


def format_location(func: Callable):
    return f"{func.__code__.co_filename}:{func.__code__.co_firstlineno}"


def format_exc(exc: Exception) -> str:
    buf = io.StringIO()
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=buf)
    return buf.getvalue()


def make_error_with_traceback(factory: Callable[[], Exception], level: int) -> Exception:

    def recurse(remaining_levels: int):
        if not remaining_levels:
            raise factory()
        else:
            recurse(remaining_levels - 1)

    try:
        recurse(level)
        return factory()  # just to satisfy linter; this will never happen
    except Exception as e:
        return e


baz_factory = _factories.FunctionFactory(baz)


@pytest.mark.parametrize(
    "uut, expected",
    [
        (
            UserFactoryDeclarationError(
                foo, "Extra parameters found in the declaration", allowed_params=["b", "c"], excessive_params=["a", "d"]
            ),
            textwrap.dedent(f"""
        Invalid declaration of resource factory {format_name(foo)!r} located in {format_location(foo)}:
        Reason:
          Extra parameters found in the declaration
        Details:
          Factory signature:
            (a: int, b: str, c: float, d: bool)
          Extra information:
            allowed_params:
              ['b', 'c']
            excessive_params:
              ['a', 'd']
        """).strip(),
        ),
        (
            UserFactoryDeclarationError(foo, "Extra parameters found in the declaration"),
            textwrap.dedent(f"""
        Invalid declaration of resource factory {format_name(foo)!r} located in {format_location(foo)}:
        Reason:
          Extra parameters found in the declaration
        Details:
          Factory signature:
            (a: int, b: str, c: float, d: bool)
        """).strip(),
        ),
        (
            UserFactoryPreconditionError(foo, injector, "Non-async injector used for async resource factory", foo=123),
            textwrap.dedent(f"""
        Precondition check failed for resource factory {format_name(foo)!r} located in {format_location(foo)}:
        Reason:
          Non-async injector used for async resource factory
        Details:
          Factory signature:
            (a: int, b: str, c: float, d: bool)
          Injector object used:
            {injector!r}
          Extra information:
            foo:
              123
        """).strip(),
        ),
        (
            UserFactoryPreconditionError(foo, injector, "Non-async injector used for async resource factory"),
            textwrap.dedent(f"""
        Precondition check failed for resource factory {format_name(foo)!r} located in {format_location(foo)}:
        Reason:
          Non-async injector used for async resource factory
        Details:
          Factory signature:
            (a: int, b: str, c: float, d: bool)
          Injector object used:
            {injector!r}
        """).strip(),
        ),
        (
            ResourceFactoryNotFoundError(int, ("foo",), "testing"),
            textwrap.dedent(f"""
        No resource factory found for query: typ={int!r}, scope=('foo',), env='testing'
        """).strip(),
        ),
        (
            OutOfScopeError(int, ("foo",), "testing", {("spam",)}),
            textwrap.dedent(f"""
        No resource factory could be accessed from the current scope for query: typ={int!r}, scope=('foo',), env='testing'
        Current scope:
          ('foo',)
        Existing scopes:
          {{('spam',)}}
        """).strip(),
        ),
        (
            IncompatibleResourceFactoryFoundError(
                int, ScopeType(), "testing", injector, baz_factory, "Async factory cannot be used by non-async injector"
            ),
            textwrap.dedent(f"""
        Incompatible resource factory found for query: typ={int!r}, scope=(), env='testing'
        Reason:
          Async factory cannot be used by non-async injector
        Details:
          Injector object:
            {injector!r}
          Resource factory object:
            {baz_factory!r}
        """).strip(),
        ),
        (
            ScopedInjectorAlreadyExistsError(injector, ("foo", "bar"), "spam"),
            textwrap.dedent(f"""
        Scoped injector named 'spam' already exists
        Details:
          Injector object:
            {injector!r}
          Injector scope:
            ('foo', 'bar')
        """).strip(),
        ),
        (
            ResourceFactoryAlreadyExistsError(int, ("foo", "bar"), "testing"),
            textwrap.dedent(f"""
        Resource factory already exists for: typ={int!r}, scope=('foo', 'bar'), env='testing'
        """).strip(),
        ),
        (
            InjectorAlreadyClosedError(injector),
            textwrap.dedent(f"""
        Cannot perform requested operation; the injector {injector!r} is already closed
        """).strip(),
        ),
    ],
)
def test_string_representations(uut, expected):
    assert str(uut) == expected


class TestIncompleteClosingError:
    def test_str(self):
        dispose_errors = {
            int: make_error_with_traceback(lambda: ValueError("a value error"), 1),
            float: make_error_with_traceback(lambda: TypeError("a type error"), 3),
        }
        int_exc_formatted = textwrap.indent(format_exc(dispose_errors[int]), "  " * 7)
        float_exc_formatted = textwrap.indent(format_exc(dispose_errors[float]), "  " * 7)
        uut = IncompleteClosingError(injector, dispose_errors)
        expected_str = textwrap.dedent(f"""
        Injector closing did not complete successfully with 2 resource disposal error(-s) found:
        Details:
          Injector object:
            {injector!r}
          Errors found (during disposal):
            for type <class 'int'>:
              {int_exc_formatted.lstrip()}
            for type <class 'float'>:
              {float_exc_formatted.lstrip()}
        """).strip()
        assert str(uut).strip() == expected_str
