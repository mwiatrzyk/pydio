import asyncio

from pydio.v1.interface import AsyncLockLike


class AsyncioBackend:
    """Implementation of the :class:`pydio.v1.Interface.AsyncBackendLike`
    protocol for :mod:`asyncio` library from Python's standard library."""

    def create_lock(self) -> AsyncLockLike:
        return asyncio.Lock()
