"""Type cast utilities for PyDIO."""

from __future__ import annotations
import inspect
from typing import Any

from pydio.v1 import _export_list
from pydio.v1.interface import T, ResourceFactoryLike

__all__ = export = _export_list.ExportList()  # type: ignore

_unset = object()


@export
def as_resource_factory(obj: Any, typ: type[T] | None = None) -> ResourceFactoryLike[T] | None:
    """Check if given object is a synchronous resource factory instance.

    Returns *obj* unchanged if it satisfies
    :class:`pydio.v1.interface.ResourceFactoryLike` protocol requirements, or
    ``None`` otherwise.

    :param obj:
        The object to cast.

    :param typ:
        Optional type parameter for the returned object.
    """
    create_method = getattr(obj, "create", _unset)
    if create_method is _unset:
        return None
    create_func = type(obj).create
    if inspect.iscoroutinefunction(create_func):
        return None
    return obj
