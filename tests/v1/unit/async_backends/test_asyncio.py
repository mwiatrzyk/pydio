import asyncio

import pytest

from pydio.v1.interface import AsyncBackendLike
from pydio.v1.async_backends.asyncio import AsyncioBackend


class TestAsyncioBackend:

    @pytest.fixture
    def uut(self):
        return AsyncioBackend()

    class TestCreateRLock:
        UUT = AsyncBackendLike

        async def test_lock_twice_from_same_task(self, uut: UUT):
            lock = uut.create_rlock()
            assert not lock.is_locked()
            assert not lock.is_owned()
            async with lock:
                async with lock:
                    assert lock.is_locked()
                    assert lock.is_owned()

        async def test_lock_twice_from_other_task(self, uut: UUT):

            async def other():
                async with lock:
                    async with lock:
                        sem.release()
                        await asyncio.sleep(0.025)
                        shared.append(123)

            shared = []
            lock = uut.create_rlock()
            sem = asyncio.Semaphore(0)
            task = asyncio.create_task(other())
            await sem.acquire()
            async with lock:
                assert shared == [123]
            await task

        async def test_when_lock_is_acquired_by_another_task_the_current_one_have_to_wait(self, uut: UUT):

            async def other():
                async with lock:
                    sem.release()
                    await asyncio.sleep(0.025)
                    shared.append(123)

            shared = []
            lock = uut.create_rlock()
            sem = asyncio.Semaphore(0)
            task = asyncio.create_task(other())
            await sem.acquire()
            async with lock:
                assert shared == [123]
            await task

        async def test_release_by_non_owning_task_is_forbidden(self, uut: UUT):

            async def task():
                lock.release()

            lock = uut.create_rlock()
            await lock.acquire()
            t = asyncio.create_task(task())
            with pytest.raises(RuntimeError, match=r"RLock.release\(\) called from a non-owning task"):
                await t

        async def test_lock_is_no_longer_owned_after_release(self, uut: UUT):
            lock = uut.create_rlock()
            await lock.acquire()
            assert lock.is_owned()
            lock.release()
            assert not lock.is_owned()
