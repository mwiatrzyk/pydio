from __future__ import annotations

from typing import Any

import pytest

from mockify.api import Mock, satisfied


@pytest.fixture
def injector_stub(generic_mock):

    class InjectorStub:
        def inject(self, typ: type | Any) -> Any:
            return generic_mock.injector.inject(typ)

    return InjectorStub()


@pytest.fixture
def async_injector_stub(generic_mock):

    class AsyncInjectorStub:
        async def inject(self, typ: type | Any) -> Any:
            return generic_mock.injector.inject(typ)

    return AsyncInjectorStub()


@pytest.fixture(
    params=[
        (),
        ("a", "b"),
    ]
)
def scope(request: pytest.FixtureRequest):
    return request.param


@pytest.fixture(params=[None, "testing"])
def env(request: pytest.FixtureRequest):
    return request.param
