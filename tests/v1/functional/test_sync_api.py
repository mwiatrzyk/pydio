import io
import contextlib

import pytest

from mockify.api import Return

from pydio.v1.api import Provider, Injector, provides, InjectorLike


@pytest.fixture
def provider(generic_mock):
    provider = Provider()

    @provides(provider, int)
    def make_int():
        return generic_mock.make_int()

    @provides(provider, io.StringIO)
    def make_stream():
        stream = io.StringIO()
        try:
            yield stream
        except Exception as e:
            generic_mock.make_stream.fail(e)
        finally:
            generic_mock.make_stream.done(stream.getvalue())

    return provider


@pytest.fixture
def injector(provider):
    return Injector(provider)


def test_make_int(injector: InjectorLike, generic_mock):
    generic_mock.make_int.expect_call().will_once(Return(123))
    value = injector.inject(int)
    assert value == 123


def test_make_stream(injector: InjectorLike, generic_mock):
    generic_mock.make_stream.done.expect_call("foo-bar-baz")
    with injector:
        injector.inject(io.StringIO).write("foo-")
        injector.inject(io.StringIO).write("bar-")
        injector.inject(io.StringIO).write("baz")


def test_make_stream_with_error(injector: InjectorLike, generic_mock):
    exc = ValueError("an error")
    generic_mock.make_stream.fail.expect_call(exc)
    generic_mock.make_stream.done.expect_call("foobar")
    with contextlib.suppress(type(exc)):
        with injector:
            injector.inject(io.StringIO).write("foo")
            injector.inject(io.StringIO).write("bar")
            raise exc
