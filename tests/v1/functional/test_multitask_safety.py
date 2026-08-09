import random
import asyncio

from mockify.api import Invoke

from pydio.v1.api import Provider, AsyncInjector, provides


async def test_async_injector_is_multitask_safe_and_executes_factory_only_once(generic_mock):
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
