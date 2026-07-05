import pytest

from mockify.api import Return, Raise

from pydio.v1._factories import (
    AsyncFunctionFactory,
    ConstantFactory,
    FunctionFactory,
    GeneratorFactory,
    AsyncGeneratorFactory,
)
from pydio.v1.interface import AsyncResourceFactoryLike, ResourceFactoryLike, SupportsAsyncInject, SupportsInject


@pytest.mark.parametrize(
    "value",
    [
        123,
        3.14159,
        [],
        {},
    ],
)
class TestConstantFactory:
    UUT = ResourceFactoryLike

    @pytest.fixture
    def uut(self, value):
        return ConstantFactory(value)

    def test_create_and_dispose_object(self, uut: UUT, injector_stub: SupportsInject, value):
        obj, disposer = uut.create(injector_stub)
        assert obj == value
        disposer.dispose()

    def test_create_always_returns_same_object_and_same_disposer(self, uut: UUT, injector_stub: SupportsInject):
        first_obj, first_disposer = uut.create(injector_stub)
        second_obj, second_disposer = uut.create(injector_stub)
        assert first_obj is second_obj
        assert first_disposer is second_disposer


class TestFunctionFactory:
    UUT = ResourceFactoryLike

    @pytest.fixture
    def uut(self, generic_mock):

        def make_object(injector):
            return generic_mock.make_object(injector)

        return FunctionFactory(make_object)

    def test_create_and_dispose_object(self, uut: UUT, injector_stub: SupportsInject, generic_mock):
        generic_mock.make_object.expect_call(injector_stub).will_once(Return(123))
        obj, disposer = uut.create(injector_stub)
        assert obj == 123
        disposer.dispose()

    def test_create_always_calls_target_and_always_returns_same_disposer(
        self, uut: UUT, injector_stub: SupportsInject, generic_mock
    ):
        generic_mock.make_object.expect_call(injector_stub).will_once(Return(123)).will_once(Return(456))
        first_obj, first_disposer = uut.create(injector_stub)
        second_obj, second_disposer = uut.create(injector_stub)
        assert first_obj == 123
        assert second_obj == 456
        assert first_disposer is second_disposer


class TestGeneratorFactory:
    UUT = ResourceFactoryLike

    @pytest.fixture
    def uut(self, generic_mock):

        def make_object(injector):
            obj = generic_mock.make_object(injector)
            try:
                yield obj
                obj.success()
            except Exception as e:
                obj.failure(e)
            finally:
                obj.done()

        return GeneratorFactory(make_object)

    def test_create_and_dispose_object(self, uut: UUT, injector_stub: SupportsInject, generic_mock):
        generic_mock.make_object.expect_call(injector_stub).will_once(Return(generic_mock.created))
        obj, disposer = uut.create(injector_stub)
        assert obj is generic_mock.created
        generic_mock.created.success.expect_call()
        generic_mock.created.done.expect_call()
        disposer.dispose()

    def test_when_dispose_signals_exception_then_generator_throws_on_yield(
        self, uut: UUT, injector_stub: SupportsInject, generic_mock
    ):
        generic_mock.make_object.expect_call(injector_stub).will_once(Return(generic_mock.created))
        obj, disposer = uut.create(injector_stub)
        assert obj is generic_mock.created
        exc = ValueError("an error")
        generic_mock.created.failure.expect_call(exc)
        generic_mock.created.done.expect_call()
        disposer.dispose(type(exc), exc)

    def test_when_factory_throws_before_yield_then_create_throws_same_error(
        self, uut: UUT, injector_stub: SupportsInject, generic_mock
    ):
        exc = ValueError("an error")
        generic_mock.make_object.expect_call(injector_stub).will_once(Raise(exc))
        with pytest.raises(ValueError) as excinfo:
            uut.create(injector_stub)
        assert excinfo.value is exc

    def test_when_there_are_two_or_more_yield_statements_then_dispose_fails_with_type_error(
        self, injector_stub: SupportsInject
    ):

        def make_object(injector):
            yield 1
            yield 2

        uut = GeneratorFactory(make_object)
        obj, disposer = uut.create(injector_stub)
        assert obj == 1
        with pytest.raises(TypeError, match="Generator .* must only yield once"):
            disposer.dispose()


class TestAsyncFunctionFactory:
    UUT = AsyncResourceFactoryLike

    @pytest.fixture
    def uut(self, generic_mock):

        async def make_object(injector):
            return generic_mock.make_object(injector)

        return AsyncFunctionFactory(make_object)

    async def test_create_and_dispose_object(self, uut: UUT, async_injector_stub: SupportsAsyncInject, generic_mock):
        generic_mock.make_object.expect_call(async_injector_stub).will_once(Return(123))
        obj, disposer = await uut.create(async_injector_stub)
        assert obj == 123
        await disposer.dispose()

    async def test_create_always_calls_target_and_always_returns_same_disposer(
        self, uut: UUT, async_injector_stub: SupportsAsyncInject, generic_mock
    ):
        generic_mock.make_object.expect_call(async_injector_stub).will_once(Return(123)).will_once(Return(456))
        first_obj, first_disposer = await uut.create(async_injector_stub)
        second_obj, second_disposer = await uut.create(async_injector_stub)
        assert first_obj == 123
        assert second_obj == 456
        assert first_disposer is second_disposer


class TestAsyncGeneratorFactory:
    UUT = AsyncResourceFactoryLike

    @pytest.fixture
    def uut(self, generic_mock):

        async def make_object(injector):
            obj = generic_mock.make_object(injector)
            try:
                yield obj
                obj.success()
            except Exception as e:
                obj.failure(e)
            finally:
                obj.done()

        return AsyncGeneratorFactory(make_object)

    async def test_create_and_dispose_object(self, uut: UUT, async_injector_stub: SupportsAsyncInject, generic_mock):
        generic_mock.make_object.expect_call(async_injector_stub).will_once(Return(generic_mock.created))
        obj, disposer = await uut.create(async_injector_stub)
        assert obj is generic_mock.created
        generic_mock.created.success.expect_call()
        generic_mock.created.done.expect_call()
        await disposer.dispose()

    async def test_when_dispose_signals_exception_then_generator_throws_on_yield(
        self, uut: UUT, async_injector_stub: SupportsAsyncInject, generic_mock
    ):
        generic_mock.make_object.expect_call(async_injector_stub).will_once(Return(generic_mock.created))
        obj, disposer = await uut.create(async_injector_stub)
        assert obj is generic_mock.created
        exc = ValueError("an error")
        generic_mock.created.failure.expect_call(exc)
        generic_mock.created.done.expect_call()
        await disposer.dispose(type(exc), exc)

    async def test_when_factory_throws_before_yield_then_create_throws_same_error(
        self, uut: UUT, async_injector_stub: SupportsAsyncInject, generic_mock
    ):
        exc = ValueError("an error")
        generic_mock.make_object.expect_call(async_injector_stub).will_once(Raise(exc))
        with pytest.raises(ValueError) as excinfo:
            await uut.create(async_injector_stub)
        assert excinfo.value is exc

    async def test_when_there_are_two_or_more_yield_statements_then_dispose_fails_with_type_error(
        self, async_injector_stub: SupportsAsyncInject
    ):

        async def make_object(injector):
            yield 1
            yield 2

        uut = AsyncGeneratorFactory(make_object)
        obj, disposer = await uut.create(async_injector_stub)
        assert obj == 1
        with pytest.raises(TypeError, match="Async generator .* must only yield once"):
            await disposer.dispose()
