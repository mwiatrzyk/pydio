from types import TracebackType

import pytest

from mockify.api import Mock, Return, satisfied, Any, Type

from pydio.v1.exc import IncompatibleFactoryProvidedError, InjectorClosedError, DuplicateScopeError
from pydio.v1.injectors import Injector, AsyncInjector
from pydio.v1.interface import InjectorLike, AsyncInjectorLike

from tests.v1.unit.stubs import (
    AsyncResourceDisposerStub,
    ResourceDisposerStub,
    ResourceFactoryStub,
    AsyncResourceFactoryStub,
)


@pytest.fixture
def provider_mock():
    mock = Mock("provider_mock")
    with satisfied(mock):
        yield mock


class TestInjector:
    @pytest.fixture
    def uut(self, provider_mock, scope, env):
        return Injector(provider_mock, scope=scope, env=env)

    def test_when_inject_called_for_a_first_time_then_factory_is_invoked(
        self, uut: InjectorLike, provider_mock, generic_mock, scope, env
    ):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert uut.inject(int) == 123

    def test_when_inject_called_for_a_second_time_for_same_type_then_cached_object_is_returned(
        self, uut: InjectorLike, provider_mock, generic_mock, scope, env
    ):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert uut.inject(int) == 123
        assert uut.inject(int) == 123

    def test_when_injector_is_closed_then_resource_is_disposed(
        self, uut: InjectorLike, provider_mock, generic_mock, scope, env
    ):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert uut.inject(int) == 123
        generic_mock.dispose_int.dispose.expect_call(None, None, None)
        uut.close()

    def test_inject_and_dispose_several_resources(self, uut: InjectorLike, provider_mock, generic_mock, scope, env):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=scope, env=env).will_once(
            Return(ResourceFactoryStub(generic_mock.create_float))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert uut.inject(int) == 123
        generic_mock.create_float.expect_call(uut).will_once(Return((3.14, generic_mock.dispose_float)))
        assert uut.inject(float) == 3.14
        generic_mock.dispose_int.dispose.expect_call(None, None, None)
        generic_mock.dispose_float.dispose.expect_call(None, None, None)
        uut.close()

    def test_close_is_idempotent(self, uut: InjectorLike, provider_mock, generic_mock, scope, env):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert uut.inject(int) == 123
        generic_mock.dispose_int.dispose.expect_call(None, None, None).times(1)
        uut.close()
        uut.close()

    def test_close_state_changes_after_close(self, uut: InjectorLike):
        assert not uut.is_closed()
        uut.close()
        assert uut.is_closed()

    def test_use_injector_as_context_manager(self, uut: InjectorLike, provider_mock, generic_mock, scope, env):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        generic_mock.dispose_int.dispose.expect_call(None, None, None).times(1)
        with uut:
            assert uut.inject(int) == 123
        assert uut.is_closed()

    def test_async_factory_is_rejected_by_synchronous_injector(
        self, uut: InjectorLike, provider_mock, generic_mock, scope, env
    ):
        factory = AsyncResourceFactoryStub(generic_mock.create_int)
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(Return(factory))
        with pytest.raises(IncompatibleFactoryProvidedError) as excinfo:
            uut.inject(int)
        assert excinfo.value.injector is uut
        assert excinfo.value.factory is factory

    def test_when_scoped_injector_ends_it_disposes_only_its_resources(self, provider_mock, generic_mock):
        uut = Injector(provider_mock)
        provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=("child",), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_float))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert uut.inject(int) == 123
        with uut.scoped("child") as child:
            generic_mock.create_float.expect_call(child).will_once(Return((3.14, generic_mock.dispose_float)))
            generic_mock.dispose_float.dispose.expect_call(None, None, None)
            assert child.inject(float) == 3.14
        assert child.is_closed()

    async def test_creating_two_scoped_injectors_with_same_scope_is_forbidden(self, uut: InjectorLike, scope):
        uut.scoped("foo")
        with pytest.raises(DuplicateScopeError) as excinfo:
            uut.scoped("foo")
        assert excinfo.value.scope == (*scope, "foo")

    def test_when_double_scoped_injector_ends_it_disposes_only_its_resources(self, provider_mock, generic_mock):
        uut = Injector(provider_mock)
        provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=("child", "grandchild"), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_float))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert uut.inject(int) == 123
        with uut.scoped("child") as child:
            with child.scoped("grandchild") as grandchild:
                generic_mock.create_float.expect_call(grandchild).will_once(Return((3.14, generic_mock.dispose_float)))
                generic_mock.dispose_float.dispose.expect_call(None, None, None)
                assert grandchild.inject(float) == 3.14

    def test_closing_root_injector_closes_all_child_injectors(self, provider_mock, generic_mock):
        uut = Injector(provider_mock)
        provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=("child",), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_float))
        )
        provider_mock.require_factory.expect_call(str, scope=("child", "grandchild"), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_str))
        )
        child = uut.scoped("child")
        grandchild = child.scoped("grandchild")
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert uut.inject(int) == 123
        generic_mock.create_float.expect_call(child).will_once(Return((3.14, generic_mock.dispose_float)))
        assert child.inject(float) == 3.14
        generic_mock.create_str.expect_call(grandchild).will_once(Return(("spam", generic_mock.dispose_str)))
        assert grandchild.inject(str) == "spam"
        generic_mock.dispose_int.dispose.expect_call(None, None, None)
        generic_mock.dispose_float.dispose.expect_call(None, None, None)
        generic_mock.dispose_str.dispose.expect_call(None, None, None)
        uut.close()

    def test_closing_root_injector_after_exception_closes_all_child_injectors_with_same_exception(
        self, provider_mock, generic_mock
    ):
        exc = ValueError("an error")
        uut = Injector(provider_mock)
        provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=("child",), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_float))
        )
        provider_mock.require_factory.expect_call(str, scope=("child", "grandchild"), env=None).will_once(
            Return(ResourceFactoryStub(generic_mock.create_str))
        )
        child = uut.scoped("child")
        grandchild = child.scoped("grandchild")
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert uut.inject(int) == 123
        generic_mock.create_float.expect_call(child).will_once(Return((3.14, generic_mock.dispose_float)))
        assert child.inject(float) == 3.14
        generic_mock.create_str.expect_call(grandchild).will_once(Return(("spam", generic_mock.dispose_str)))
        assert grandchild.inject(str) == "spam"
        generic_mock.dispose_int.dispose.expect_call(type(exc), exc, Any())
        generic_mock.dispose_float.dispose.expect_call(type(exc), exc, Any())
        generic_mock.dispose_str.dispose.expect_call(type(exc), exc, Any())
        with pytest.raises(ValueError):
            with uut:
                raise exc

    @pytest.mark.parametrize(
        "op",
        [
            lambda injector: injector.scoped("foo"),
            lambda injector: injector.inject(int),
        ],
    )
    def test_operating_on_a_closed_injector_is_forbidden(self, uut: InjectorLike, op):
        uut.close()
        assert uut.is_closed()
        with pytest.raises(InjectorClosedError):
            op(uut)

    def test_disposer_is_called_with_exc_info_if_error_happens_inside_context_manager(
        self, provider_mock, generic_mock
    ):
        uut = Injector(provider_mock)
        exc = ValueError("dummy error")
        generic_mock.dispose_int.dispose.expect_call(type(exc), exc, Type(TracebackType))
        with pytest.raises(ValueError):
            with uut:
                provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
                    Return(ResourceFactoryStub(generic_mock.create_int))
                )
                generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
                uut.inject(int)
                raise exc


class TestAsyncInjector:
    @pytest.fixture
    async def uut(self, provider_mock, scope, env):
        return AsyncInjector(provider_mock, scope=scope, env=env)

    @pytest.fixture(
        params=[
            (ResourceFactoryStub, ResourceDisposerStub),
            (AsyncResourceFactoryStub, AsyncResourceDisposerStub),
        ]
    )
    def resource_factory_disposer_cls_pair(self, request: pytest.FixtureRequest):
        return request.param

    @pytest.fixture
    def resource_factory_cls(self, resource_factory_disposer_cls_pair: tuple):
        return resource_factory_disposer_cls_pair[0]

    @pytest.fixture
    def resource_disposer_cls(self, resource_factory_disposer_cls_pair: tuple):
        return resource_factory_disposer_cls_pair[1]

    async def test_calling_inject_for_a_first_time_creates_and_returns_resource(
        self, uut: AsyncInjectorLike, provider_mock, resource_factory_cls, generic_mock, scope, env
    ):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(resource_factory_cls(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert (await uut.inject(int)) == 123

    async def test_when_inject_called_for_a_second_time_for_same_type_then_cached_object_is_returned(
        self, uut: AsyncInjectorLike, provider_mock, resource_factory_cls, generic_mock, scope, env
    ):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(resource_factory_cls(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(Return((123, generic_mock.dispose_int)))
        assert (await uut.inject(int)) == 123
        assert (await uut.inject(int)) == 123

    async def test_when_injector_is_closed_then_resource_is_disposed(
        self,
        uut: AsyncInjectorLike,
        provider_mock,
        resource_factory_cls,
        resource_disposer_cls,
        generic_mock,
        scope,
        env,
    ):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(resource_factory_cls(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(
            Return((123, resource_disposer_cls(generic_mock.dispose_int)))
        )
        assert (await uut.inject(int)) == 123
        generic_mock.dispose_int.expect_call(None, None, None)
        await uut.close()

    async def test_inject_and_dispose_several_resources(
        self,
        uut: AsyncInjectorLike,
        provider_mock,
        resource_factory_cls,
        resource_disposer_cls,
        generic_mock,
        scope,
        env,
    ):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(resource_factory_cls(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=scope, env=env).will_once(
            Return(resource_factory_cls(generic_mock.create_float))
        )
        generic_mock.create_int.expect_call(uut).will_once(
            Return((123, resource_disposer_cls(generic_mock.dispose_int)))
        )
        assert (await uut.inject(int)) == 123
        generic_mock.create_float.expect_call(uut).will_once(
            Return((3.14, resource_disposer_cls(generic_mock.dispose_float)))
        )
        assert (await uut.inject(float)) == 3.14
        generic_mock.dispose_int.expect_call(None, None, None)
        generic_mock.dispose_float.expect_call(None, None, None)
        await uut.close()

    async def test_close_is_idempotent(
        self,
        uut: AsyncInjectorLike,
        provider_mock,
        resource_factory_cls,
        resource_disposer_cls,
        generic_mock,
        scope,
        env,
    ):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(resource_factory_cls(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(
            Return((123, resource_disposer_cls(generic_mock.dispose_int)))
        )
        assert (await uut.inject(int)) == 123
        generic_mock.dispose_int.expect_call(None, None, None).times(1)
        await uut.close()
        await uut.close()

    async def test_close_state_changes_after_close(self, uut: AsyncInjectorLike):
        assert not uut.is_closed()
        await uut.close()
        assert uut.is_closed()

    async def test_use_injector_as_context_manager(
        self,
        uut: AsyncInjectorLike,
        provider_mock,
        resource_factory_cls,
        resource_disposer_cls,
        generic_mock,
        scope,
        env,
    ):
        provider_mock.require_factory.expect_call(int, scope=scope, env=env).will_once(
            Return(resource_factory_cls(generic_mock.create_int))
        )
        generic_mock.create_int.expect_call(uut).will_once(
            Return((123, resource_disposer_cls(generic_mock.dispose_int)))
        )
        generic_mock.dispose_int.expect_call(None, None, None).times(1)
        async with uut:
            assert (await uut.inject(int)) == 123
        assert uut.is_closed()

    async def test_when_scoped_injector_ends_it_disposes_only_its_resources(self, provider_mock, generic_mock):
        uut = AsyncInjector(provider_mock)
        provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=("child",), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_float))
        )
        generic_mock.create_int.expect_call(uut).will_once(
            Return((123, AsyncResourceDisposerStub(generic_mock.dispose_int)))
        )
        assert (await uut.inject(int)) == 123
        async with uut.scoped("child") as child:
            generic_mock.create_float.expect_call(child).will_once(
                Return((3.14, AsyncResourceDisposerStub(generic_mock.dispose_float)))
            )
            generic_mock.dispose_float.expect_call(None, None, None)
            assert (await child.inject(float)) == 3.14
        assert child.is_closed()

    async def test_creating_two_scoped_injectors_with_same_scope_is_forbidden(self, uut: AsyncInjectorLike, scope):
        uut.scoped("foo")
        with pytest.raises(DuplicateScopeError) as excinfo:
            uut.scoped("foo")
        assert excinfo.value.scope == (*scope, "foo")

    async def test_when_double_scoped_injector_ends_it_disposes_only_its_resources(self, provider_mock, generic_mock):
        uut = AsyncInjector(provider_mock)
        provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=("child", "grandchild"), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_float))
        )
        generic_mock.create_int.expect_call(uut).will_once(
            Return((123, AsyncResourceDisposerStub(generic_mock.dispose_int)))
        )
        assert (await uut.inject(int)) == 123
        async with uut.scoped("child") as child:
            async with child.scoped("grandchild") as grandchild:
                generic_mock.create_float.expect_call(grandchild).will_once(
                    Return((3.14, AsyncResourceDisposerStub(generic_mock.dispose_float)))
                )
                generic_mock.dispose_float.expect_call(None, None, None)
                assert (await grandchild.inject(float)) == 3.14

    async def test_closing_root_injector_closes_all_child_injectors(self, provider_mock, generic_mock):
        uut = AsyncInjector(provider_mock)
        provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=("child",), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_float))
        )
        provider_mock.require_factory.expect_call(str, scope=("child", "grandchild"), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_str))
        )
        child = uut.scoped("child")
        grandchild = child.scoped("grandchild")
        generic_mock.create_int.expect_call(uut).will_once(
            Return((123, AsyncResourceDisposerStub(generic_mock.dispose_int)))
        )
        assert (await uut.inject(int)) == 123
        generic_mock.create_float.expect_call(child).will_once(
            Return((3.14, AsyncResourceDisposerStub(generic_mock.dispose_float)))
        )
        assert (await child.inject(float)) == 3.14
        generic_mock.create_str.expect_call(grandchild).will_once(
            Return(("spam", AsyncResourceDisposerStub(generic_mock.dispose_str)))
        )
        assert (await grandchild.inject(str)) == "spam"
        generic_mock.dispose_int.expect_call(None, None, None)
        generic_mock.dispose_float.expect_call(None, None, None)
        generic_mock.dispose_str.expect_call(None, None, None)
        await uut.close()

    async def test_closing_root_injector_after_exception_closes_all_child_injectors_with_same_exception(
        self, provider_mock, generic_mock
    ):
        exc = ValueError("an error")
        uut = AsyncInjector(provider_mock)
        provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_int))
        )
        provider_mock.require_factory.expect_call(float, scope=("child",), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_float))
        )
        provider_mock.require_factory.expect_call(str, scope=("child", "grandchild"), env=None).will_once(
            Return(AsyncResourceFactoryStub(generic_mock.create_str))
        )
        child = uut.scoped("child")
        grandchild = child.scoped("grandchild")
        generic_mock.create_int.expect_call(uut).will_once(
            Return((123, AsyncResourceDisposerStub(generic_mock.dispose_int)))
        )
        assert (await uut.inject(int)) == 123
        generic_mock.create_float.expect_call(child).will_once(
            Return((3.14, AsyncResourceDisposerStub(generic_mock.dispose_float)))
        )
        assert (await child.inject(float)) == 3.14
        generic_mock.create_str.expect_call(grandchild).will_once(
            Return(("spam", AsyncResourceDisposerStub(generic_mock.dispose_str)))
        )
        assert (await grandchild.inject(str)) == "spam"
        generic_mock.dispose_int.expect_call(type(exc), exc, Any())
        generic_mock.dispose_float.expect_call(type(exc), exc, Any())
        generic_mock.dispose_str.expect_call(type(exc), exc, Any())
        with pytest.raises(ValueError):
            async with uut:
                raise exc

    async def test_scoped_cannot_be_called_on_closed_injector(self, uut: AsyncInjectorLike):
        await uut.close()
        assert uut.is_closed()
        with pytest.raises(InjectorClosedError) as excinfo:
            uut.scoped("foo")
        assert excinfo.value.injector is uut

    async def test_inject_cannot_be_called_on_closed_injector(self, uut: AsyncInjectorLike):
        await uut.close()
        assert uut.is_closed()
        with pytest.raises(InjectorClosedError) as excinfo:
            await uut.inject(int)
        assert excinfo.value.injector is uut

    async def test_disposer_is_called_with_exc_info_if_error_happens_inside_context_manager(
        self, provider_mock, generic_mock
    ):
        uut = AsyncInjector(provider_mock)
        exc = ValueError("dummy error")
        generic_mock.dispose_int.expect_call(type(exc), exc, Type(TracebackType))
        with pytest.raises(ValueError):
            async with uut:
                provider_mock.require_factory.expect_call(int, scope=tuple(), env=None).will_once(
                    Return(AsyncResourceFactoryStub(generic_mock.create_int))
                )
                generic_mock.create_int.expect_call(uut).will_once(
                    Return((123, AsyncResourceDisposerStub(generic_mock.dispose_int)))
                )
                await uut.inject(int)
                raise exc
