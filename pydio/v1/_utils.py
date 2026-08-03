import functools
import inspect
import textwrap
from typing import Any, Callable, get_type_hints

_unset = object()


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


def format_detailed_error(
    out: list[str], data: dict, *, indent_char: str = "", indent_level: int = 0, width: int = 120
) -> None:
    for k, v in data.items():
        if v is None:
            continue
        label_indent = indent_char * indent_level
        out.append(f"{label_indent}{k}:")
        if isinstance(v, dict):
            return format_detailed_error(out, v, indent_char=indent_char, indent_level=indent_level + 1, width=width)
        value_indent = indent_char * (indent_level + 1)
        out.extend(textwrap.wrap(str(v), width=width, initial_indent=value_indent, subsequent_indent=value_indent))


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
