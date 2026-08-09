from __future__ import annotations

import asyncio
import collections

from pydio.v1.interface import AsyncRLockLike


class AsyncioBackend:
    """Implementation of the :class:`pydio.v1.Interface.AsyncBackendLike`
    protocol for the **asyncio** library from Python's standard library.

    This backend is used as a default when async injector is used.
    """

    def create_rlock(self) -> AsyncRLockLike:
        return self._RLock()

    class _RLock:

        def __init__(self):
            self.__waiters = collections.deque[asyncio.Event]()
            self.__count = 0
            self.__owner: asyncio.Task | None = None

        async def acquire(self) -> None:
            current_task = asyncio.current_task()
            owning_task = self.__owner
            if owning_task is None:
                self.__owner = current_task
            elif owning_task is not current_task:
                waiter = asyncio.Event()
                self.__waiters.append(waiter)
                await waiter.wait()
                self.__owner = current_task
            self.__count += 1

        def release(self) -> None:
            if not self.is_owned():
                raise RuntimeError(f"{self.__class__.__name__}.release() called from a non-owning task")
            self.__count -= 1
            if self.__count == 0:
                if len(self.__waiters) > 0:
                    self.__waiters.popleft().set()
                self.__owner = None

        def is_locked(self) -> bool:
            return self.__count > 0

        def is_owned(self) -> bool:
            return self.__owner is asyncio.current_task()

        async def __aenter__(self):
            await self.acquire()

        async def __aexit__(self, exc_type, exc, tb):
            self.release()
