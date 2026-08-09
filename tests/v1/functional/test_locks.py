import random
import threading
import time
import asyncio

from mockify.api import Invoke

from pydio.v1.api import Provider, Injector, AsyncInjector, provides


def test_injector_is_thread_safe_and_executes_factory_only_once(generic_mock):
    provider = Provider()

    @provides(provider, int)
    def make_int():
        time.sleep(random.random() * 0.025)
        return generic_mock.make_int()

    injector = Injector(provider)

    def perform_injection():
        output.append(injector.inject(int))

    generic_mock.make_int.expect_call().will_once(Invoke(lambda: random.randint(1, 65535)))
    num_threads = 100
    threads: list[threading.Thread] = []
    output = []
    for _ in range(num_threads):
        threads.append(threading.Thread(target=perform_injection))
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    for i in range(num_threads - 1):
        assert output[i] == output[i + 1]


async def test_async_injector_is_multiple_coroutine_safe_and_executes_factory_only_once(generic_mock):
    provider = Provider()

    @provides(provider, int)
    async def make_int():
        await asyncio.sleep(random.random() * 0.025)
        return generic_mock.make_int()

    injector = AsyncInjector(provider)

    async def perform_injection():
        output.append(await injector.inject(int))

    generic_mock.make_int.expect_call().will_once(Invoke(lambda: random.randint(1, 65535)))
    num_coroutines = 100
    output = []
    tasks: list[asyncio.Task] = []
    for _ in range(num_coroutines):
        tasks.append(asyncio.create_task(perform_injection()))
    for task in tasks:
        await task
    for i in range(num_coroutines - 1):
        assert output[i] == output[i + 1]
