import functools
import inspect
import textwrap
from typing import Any, Callable, get_type_hints


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
