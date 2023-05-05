# ---------------------------------------------------------------------------
# tests/functional/test_using_multiple_threads.py
#
# Copyright (C) 2021 - 2023 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import multiprocessing
import random
import string
import threading
import time

from pydio.api import Injector, Provider


def test_factory_function_is_called_once_for_multiple_threads():

    def factory():
        nonlocal count
        count += 1
        return count

    def run():
        for _ in range(10):
            for key in string.ascii_uppercase:
                time.sleep(0.0001 + random.random() * 0.0009)
                injector.inject(key)

    count = 0
    provider = Provider()
    for key in string.ascii_uppercase:
        provider.register_func(key, factory)
    injector = Injector(provider)

    threads = [
        threading.Thread(target=run)
        for _ in range(multiprocessing.cpu_count())
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert count == len(string.ascii_uppercase)
