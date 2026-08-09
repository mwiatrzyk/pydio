import pytest


@pytest.fixture(params=["manual", "auto"])
def mode(request: pytest.FixtureRequest):
    return request.param
