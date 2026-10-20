import time
import random
import threading

from mockify.api import Invoke

from pydio.v1.api import Provider, Injector, provides


def test_injector_is_multithread_safe_and_executes_factory_only_once(generic_mock):
    provider = Provider()

    @provides(provider, int)
    def make_int():
        time.sleep(random.random() * 0.025)
        return generic_mock.make_int()

    def perform_injection():
        output.append(injector.inject(int))

    generic_mock.make_int.expect_call().will_once(Invoke(lambda: random.randint(1, 65535)))
    num_threads = 100
    threads: list[threading.Thread] = []
    output = []
    injector = Injector(provider)
    for _ in range(num_threads):
        threads.append(threading.Thread(target=perform_injection))
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    for i in range(num_threads - 1):
        assert output[i] == output[i + 1]
