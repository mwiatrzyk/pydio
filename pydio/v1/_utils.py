from __future__ import annotations

import collections.abc
import functools
import inspect
import io
import textwrap
import traceback
from typing import Annotated, Any, AsyncGenerator, Callable, Generator, Hashable, TypeVar, get_type_hints

from typing_extensions import TypeIs

_unset = object()

T = TypeVar("T")


def unpack_partial(obj: Any) -> Any:
    """If given *obj* is instance of :class:`functools.partial`, then return
    function object it wraps or otherwise return *obj*."""
    if isinstance(obj, functools.partial):
        return obj.func
    return obj


@functools.lru_cache()
def get_func_signature(func: Callable) -> inspect.Signature:
    """Get signature of given function with unpacked types."""
    sig = inspect.signature(func)
    hints = get_type_hints(func, include_extras=True)
    return sig.replace(
        parameters=[p.replace(annotation=hints.get(name, p.annotation)) for name, p in sig.parameters.items()],
        return_annotation=hints.get("return", sig.return_annotation),
    )


def get_func_name(func: Callable) -> str:
    """Get name of given function."""
    return func.__name__


def get_func_location(func: Callable) -> str:
    """Get the location, as ``[file]:[line]`` string, of the given function."""
    return f"{func.__code__.co_filename}:{func.__code__.co_firstlineno}"


def format_detailed_error(
    out: list[str],
    data: dict,
    *,
    indent_char: str = "",
    width: int = 120,
    exclude_none: bool = True,
    recurse_list: bool = False,
) -> None:
    """Function for producing pretty-formatted error details for exceptions.

    :param out:
        Output list to populate with text rows.

    :param data:
        Mapping with data to be rendered.

    :param indent_char:
        Indentation character to use per single level of indentation.

    :param width:
        Text row maximum length.

        Text strings longer than this are splitted into several rows.

    :param exclude_none:
        Flag to exclude ``None`` from the output.

    :param recurse_list:
        Flag enabling recursion into lists.

        If not set, lists are displayed as ``str(l)``, where ``l`` is the list
        from *data* mapping. Otherwise lists are interpreted as part of data
        and can be used for printing arrays of objects.
    """

    def format_dict(source: dict, depth: int):
        for k, v in source.items():
            if exclude_none and v is None:
                continue
            is_dict = isinstance(v, dict)
            if is_dict and not v:
                continue
            label_indent = indent_char * depth
            out.append(f"{label_indent}{k}:")
            if is_dict:
                return format_dict(v, depth + 1)
            if isinstance(v, list) and recurse_list:
                return format_list(v, depth + 1)
            value_indent = indent_char * (depth + 1)
            if isinstance(v, Exception):
                out.append(textwrap.indent(format_exc(v), value_indent))
            else:
                out.extend(
                    textwrap.wrap(str(v), width=width, initial_indent=value_indent, subsequent_indent=value_indent)
                )

    def format_list(source: list, depth: int):
        for item in source:
            if isinstance(item, dict):
                format_dict(item, depth)

    format_dict(data, 0)


def format_exc(exc: Exception) -> str:
    """Format exception and associated traceback to string."""
    buf = io.StringIO()
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=buf)
    return buf.getvalue()


def not_used(*args) -> None:
    """A no-op helper for use with ignored function arguments."""


def has_method(obj: Any, name: str) -> bool:
    """Check if given object has method with given name which is a normal
    Python function declared as ``def X()`` (i.e. not a coroutine).

    :param obj:
        The object to check.

    :param name:
        Method's name.
    """
    bound_method = getattr(obj, name, _unset)
    if bound_method is _unset:
        return False
    unbound_method = getattr(type(obj), name, _unset)
    if unbound_method is _unset:
        return False
    return inspect.isfunction(unbound_method) and not inspect.iscoroutinefunction(unbound_method)


def has_coroutine_method(obj: Any, name: str) -> bool:
    """Check if given object has method with given name which is a
    coroutine.

    :param obj:
        The object to check.

    :param name:
        Method's name.
    """
    bound_method = getattr(obj, name, _unset)
    if bound_method is _unset:
        return False
    unbound_method = getattr(type(obj), name, _unset)
    if unbound_method is _unset:
        return False
    return inspect.iscoroutinefunction(unbound_method)


def is_async_generator(obj: object, typ: type[T] | None = None) -> TypeIs[AsyncGenerator[T]]:
    """Check if given object is an async generator object.

    :param obj:
        The object to check.

    :param typ:
        The optional type to refine returned check.
    """
    return isinstance(obj, collections.abc.AsyncGenerator)


def is_generator(obj: object, typ: type[T] | None = None) -> TypeIs[Generator[T]]:
    """Check if given object is a generator object.

    :param obj:
        The object to check.

    :param typ:
        The optional type to refine returned check.
    """
    return isinstance(obj, collections.abc.Generator)


@functools.lru_cache(128)
def build_annotated(typ: Hashable, *metadata: Hashable) -> Any:
    """Helper for building :obj:`typing.Annotated` special forms in the
    runtime.

    It uses LRU caching, keeping most recent 128 types in cache.
    """
    return Annotated.__class_getitem__((typ, *metadata))  # type: ignore
