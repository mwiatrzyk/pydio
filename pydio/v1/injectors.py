"""Module containing injector types."""

from __future__ import annotations

import threading
from typing import Any

from pydio.v1 import _export_list
from pydio.v1.interface import T, EnvType, SupportsRequireFactory, ResourceDisposerLike

__all__ = export = _export_list.ExportList()  # type: ignore


@export
class Injector:
    def __init__(self, provider: SupportsRequireFactory, *, env: EnvType = None):
        self.__provider = provider
        self.__env = env
        self.__cache: dict[Any, tuple[Any, ResourceDisposerLike]] = {}
        self.__lock = threading.RLock()

    def inject(self, typ: type[T] | Any) -> T:
        return typ()
        # cached = self.__cache.get(typ)
        # if cached is not None:
        #     return cached[0]
        # with self.__lock:
        #     cached = self.__cache.get(typ)
        #     if cached is not None:
        #         return cached[0]
        #     constructors = self.__provider.get_constructors(typ, env=self.__env)
        #     assert len(constructors) == 1
        #     constructor = as_resource_creator(constructors[0])
        #     assert constructor is not None
        #     obj, destructor = constructor.create()
        #     self.__cache[typ] = (obj, destructor)
        #     return obj


@export
class AsyncInjector:
    pass
