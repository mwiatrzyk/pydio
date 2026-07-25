import inspect
import textwrap

import pytest

from mockify.api import Return

from pydio.v1.exc import FactoryDeclarationError, IncompatibleInjectorUsedError
from pydio.v1.interface import SupportsAsyncInject, SupportsInject
from pydio.v1._adapters import adapt_func_for_manual_mode, adapt_func_for_auto_mode


class TestAdaptFuncForManualMode:
    def test_adapting_fails_if_wrong_type_is_used_as_a_function_to_wrap(self):
        with pytest.raises(TypeError):
            adapt_func_for_manual_mode(object(), int)

    def test_adapting_fails_if_incorrect_arguments_are_used_in_function_declaration(self):

        def make_object(foo, bar, baz):
            return 123

        with pytest.raises(FactoryDeclarationError) as excinfo:
            adapt_func_for_manual_mode(make_object, int)
        assert excinfo.value.reason == (
            "Parameters out of allowed set are found in function declaration; "
            "extra found: ['bar', 'baz', 'foo'], "
            "allowed set: ['env', 'injector', 'scope', 'typ']"
        )
        assert excinfo.value.func is make_object

    async def test_calling_async_generator_factory_with_injector_param_raises_error_if_non_async_injector_is_passed(
        self, injector_stub
    ):

        async def make_object(injector):
            yield 123

        adapted = adapt_func_for_manual_mode(make_object, int)
        assert inspect.isasyncgenfunction(adapted)
        gen = adapted(injector_stub)
        with pytest.raises(IncompatibleInjectorUsedError) as excinfo:
            await gen.__anext__()
        assert excinfo.value.factory is make_object
        assert excinfo.value.injector == injector_stub

    async def test_calling_async_function_factory_with_injector_param_raises_error_if_non_async_injector_is_passed(
        self, injector_stub
    ):

        async def make_object(injector):
            return 123

        adapted = adapt_func_for_manual_mode(make_object, int)
        assert inspect.iscoroutinefunction(adapted)
        with pytest.raises(IncompatibleInjectorUsedError) as excinfo:
            await adapted(injector_stub)
        assert excinfo.value.factory is make_object
        assert excinfo.value.injector is injector_stub

    def test_calling_non_async_generator_factory_with_injector_param_raises_error_if_async_injector_is_passed(
        self, async_injector_stub
    ):

        def make_object(injector):
            yield 123

        adapted = adapt_func_for_manual_mode(make_object, int)
        assert inspect.isgeneratorfunction(adapted)
        gen = adapted(async_injector_stub)
        with pytest.raises(IncompatibleInjectorUsedError) as excinfo:
            next(gen)
        assert excinfo.value.factory is make_object
        assert excinfo.value.injector == async_injector_stub

    def test_calling_non_async_function_factory_with_injector_param_raises_error_if_async_injector_is_passed(
        self, async_injector_stub
    ):

        def make_object(injector):
            return 123

        adapted = adapt_func_for_manual_mode(make_object, int)
        assert inspect.isfunction(adapted)
        with pytest.raises(IncompatibleInjectorUsedError) as excinfo:
            adapted(async_injector_stub)
        assert excinfo.value.factory is make_object
        assert excinfo.value.injector is async_injector_stub

    class TestAsyncGeneratorFunction:
        async def test_adapt_with_no_args(self, async_injector_stub: SupportsAsyncInject, scope, env, generic_mock):

            async def make_object():
                yield generic_mock()

            adapted = adapt_func_for_manual_mode(make_object, int, scope=scope, env=env)
            assert inspect.isasyncgenfunction(adapted)
            gen = adapted(async_injector_stub)
            generic_mock.expect_call().will_once(Return(123))
            assert (await gen.__anext__()) == 123

        async def test_adapt_with_all_args(self, async_injector_stub: SupportsAsyncInject, scope, env, generic_mock):

            async def make_object(injector, typ, scope, env):
                yield generic_mock(injector, typ, scope, env)

            adapted = adapt_func_for_manual_mode(make_object, int, scope=scope, env=env)
            assert inspect.isasyncgenfunction(adapted)
            gen = adapted(async_injector_stub)
            generic_mock.expect_call(async_injector_stub, int, scope, env).will_once(Return(123))
            assert (await gen.__anext__()) == 123

        @pytest.mark.parametrize("argname", ["injector", "typ", "scope", "env"])
        def test_adapt_with_selected_arg(
            self, async_injector_stub: SupportsAsyncInject, scope, env, generic_mock, argname
        ):
            testcode = textwrap.dedent(f"""
            import asyncio

            async def main():
                async def make_object({argname}):
                    yield generic_mock({argname})

                adapted = adapt_func_for_manual_mode(make_object, typ, scope=scope, env=env)
                assert inspect.isasyncgenfunction(adapted)
                gen = adapted(injector)
                generic_mock.expect_call({argname}).will_once(Return(123))
                assert (await gen.__anext__()) == 123

            asyncio.run(main())
            """)
            g = globals()
            g.update(
                {"typ": int, "injector": async_injector_stub, "scope": scope, "env": env, "generic_mock": generic_mock}
            )
            exec(testcode, g)

    class TestAsyncFunction:
        async def test_adapt_with_no_args(self, async_injector_stub: SupportsAsyncInject, scope, env, generic_mock):

            async def make_object():
                return generic_mock()

            adapted = adapt_func_for_manual_mode(make_object, int, scope=scope, env=env)
            assert inspect.iscoroutinefunction(adapted)
            generic_mock.expect_call().will_once(Return(123))
            assert (await adapted(async_injector_stub)) == 123

        async def test_adapt_with_all_args(self, async_injector_stub: SupportsAsyncInject, scope, env, generic_mock):

            async def make_object(injector, typ, scope, env):
                return generic_mock(injector, typ, scope, env)

            adapted = adapt_func_for_manual_mode(make_object, int, scope=scope, env=env)
            assert inspect.iscoroutinefunction(adapted)
            generic_mock.expect_call(async_injector_stub, int, scope, env).will_once(Return(123))
            assert (await adapted(async_injector_stub)) == 123

        @pytest.mark.parametrize("argname", ["injector", "typ", "scope", "env"])
        def test_adapt_with_selected_arg(
            self, async_injector_stub: SupportsAsyncInject, scope, env, generic_mock, argname
        ):
            testcode = textwrap.dedent(f"""
            import asyncio

            async def main():
                async def make_object({argname}):
                    return generic_mock({argname})

                adapted = adapt_func_for_manual_mode(make_object, typ, scope=scope, env=env)
                assert inspect.iscoroutinefunction(adapted)
                generic_mock.expect_call({argname}).will_once(Return(123))
                assert (await adapted(injector)) == 123

            asyncio.run(main())
            """)
            g = globals()
            g.update(
                {"typ": int, "injector": async_injector_stub, "scope": scope, "env": env, "generic_mock": generic_mock}
            )
            exec(testcode, g)

    class TestGeneratorFunction:
        def test_adapt_with_no_args(self, injector_stub: SupportsInject, scope, env, generic_mock):

            def make_object():
                yield generic_mock()

            adapted = adapt_func_for_manual_mode(make_object, int, scope=scope, env=env)
            assert inspect.isgeneratorfunction(adapted)
            gen = adapted(injector_stub)
            generic_mock.expect_call().will_once(Return(123))
            assert next(gen) == 123

        def test_adapt_with_all_args(self, injector_stub: SupportsInject, scope, env, generic_mock):

            def make_object(injector, typ, scope, env):
                yield generic_mock(injector, typ, scope, env)

            adapted = adapt_func_for_manual_mode(make_object, int, scope=scope, env=env)
            assert inspect.isgeneratorfunction(adapted)
            gen = adapted(injector_stub)
            generic_mock.expect_call(injector_stub, int, scope, env).will_once(Return(123))
            assert next(gen) == 123

        @pytest.mark.parametrize("argname", ["injector", "typ", "scope", "env"])
        def test_adapt_with_selected_arg(self, injector_stub: SupportsInject, scope, env, generic_mock, argname):
            testcode = textwrap.dedent(f"""
            def make_object({argname}):
                yield generic_mock({argname})

            adapted = adapt_func_for_manual_mode(make_object, typ, scope=scope, env=env)
            assert inspect.isgeneratorfunction(adapted)
            generic_mock.expect_call({argname}).will_once(Return(123))
            gen = adapted(injector)
            assert next(gen) == 123
            """)
            g = globals()
            g.update({"typ": int, "injector": injector_stub, "scope": scope, "env": env, "generic_mock": generic_mock})
            exec(testcode, g)

    class TestFunction:
        def test_adapt_with_no_args(self, injector_stub: SupportsInject, scope, env, generic_mock):

            def make_object():
                return generic_mock()

            adapted = adapt_func_for_manual_mode(make_object, int, scope=scope, env=env)
            assert inspect.isfunction(adapted)
            generic_mock.expect_call().will_once(Return(123))
            assert adapted(injector_stub) == 123

        def test_adapt_with_all_args(self, injector_stub: SupportsInject, scope, env, generic_mock):

            def make_object(injector, typ, scope, env):
                return generic_mock(injector, typ, scope, env)

            adapted = adapt_func_for_manual_mode(make_object, int, scope=scope, env=env)
            assert inspect.isfunction(adapted)
            generic_mock.expect_call(injector_stub, int, scope, env).will_once(Return(123))
            assert adapted(injector_stub) == 123

        @pytest.mark.parametrize("argname", ["injector", "typ", "scope", "env"])
        def test_adapt_with_selected_arg(self, injector_stub: SupportsInject, scope, env, generic_mock, argname):
            testcode = textwrap.dedent(f"""
            def make_object({argname}):
                return generic_mock({argname})

            adapted = adapt_func_for_manual_mode(make_object, typ, scope=scope, env=env)
            assert inspect.isfunction(adapted)
            generic_mock.expect_call({argname}).will_once(Return(123))
            assert adapted(injector) == 123
            """)
            g = globals()
            g.update({"typ": int, "injector": injector_stub, "scope": scope, "env": env, "generic_mock": generic_mock})
            exec(testcode, g)


class TestAdaptFuncForAutoMode:
    def test_adapting_fails_if_wrong_type_is_used_as_a_function_to_wrap(self):
        with pytest.raises(TypeError):
            adapt_func_for_manual_mode(object(), int)

    def test_adapting_fails_if_target_function_has_annotations_missing(self):

        def make_object(foo: int, bar: float, baz):
            return 123

        with pytest.raises(FactoryDeclarationError):
            adapt_func_for_auto_mode(make_object)

    async def test_running_async_func_with_non_async_injector_causes_error(self, injector_stub: SupportsInject):

        async def make_object(foo: int) -> int:
            return 123

        adapted = adapt_func_for_auto_mode(make_object)
        assert inspect.iscoroutinefunction(adapted)
        with pytest.raises(IncompatibleInjectorUsedError) as excinfo:
            await adapted(injector_stub)
        assert excinfo.value.factory is make_object
        assert excinfo.value.injector is injector_stub

    async def test_running_non_async_func_with_async_injector_causes_error(
        self, async_injector_stub: SupportsAsyncInject
    ):

        def make_object(foo: int) -> int:
            return 123

        adapted = adapt_func_for_auto_mode(make_object)
        assert inspect.isfunction(adapted)
        with pytest.raises(IncompatibleInjectorUsedError) as excinfo:
            adapted(async_injector_stub)
        assert excinfo.value.factory is make_object
        assert excinfo.value.injector is async_injector_stub

    class TestAsyncGeneratorFunction:
        async def test_adapt_with_no_args(self, async_injector_stub: SupportsAsyncInject, generic_mock):

            async def make_object():
                yield generic_mock()

            adapted = adapt_func_for_auto_mode(make_object)
            assert inspect.isasyncgenfunction(adapted)
            gen = adapted(async_injector_stub)
            generic_mock.expect_call().will_once(Return(123))
            assert (await gen.__anext__()) == 123

        async def test_adapt_with_args(self, async_injector_stub: SupportsAsyncInject, generic_mock):

            async def make_object(foo: int, bar: float, baz: str):
                yield generic_mock(foo, bar, baz)

            adapted = adapt_func_for_auto_mode(make_object)
            assert inspect.isasyncgenfunction(adapted)
            gen = adapted(async_injector_stub)
            generic_mock.injector.inject.expect_call(int).will_once(Return(123))
            generic_mock.injector.inject.expect_call(float).will_once(Return(3.14))
            generic_mock.injector.inject.expect_call(str).will_once(Return("spam"))
            generic_mock.expect_call(123, 3.14, "spam").will_once(Return(123))
            assert (await gen.__anext__()) == 123

    class TestAsyncFunction:
        async def test_adapt_with_no_args(self, async_injector_stub: SupportsAsyncInject, generic_mock):

            async def make_object():
                return generic_mock()

            adapted = adapt_func_for_auto_mode(make_object)
            assert inspect.iscoroutinefunction(adapted)
            generic_mock.expect_call().will_once(Return(123))
            assert (await adapted(async_injector_stub)) == 123

        async def test_adapt_with_args(self, async_injector_stub: SupportsAsyncInject, generic_mock):

            async def make_object(foo: int, bar: float, baz: str):
                return generic_mock(foo, bar, baz)

            adapted = adapt_func_for_auto_mode(make_object)
            assert inspect.iscoroutinefunction(adapted)
            generic_mock.injector.inject.expect_call(int).will_once(Return(123))
            generic_mock.injector.inject.expect_call(float).will_once(Return(3.14))
            generic_mock.injector.inject.expect_call(str).will_once(Return("spam"))
            generic_mock.expect_call(123, 3.14, "spam").will_once(Return(123))
            assert (await adapted(async_injector_stub)) == 123

    class TestGeneratorFunction:
        def test_adapt_with_no_args(self, injector_stub: SupportsInject, generic_mock):

            def make_object():
                yield generic_mock()

            adapted = adapt_func_for_auto_mode(make_object)
            assert inspect.isgeneratorfunction(adapted)
            gen = adapted(injector_stub)
            generic_mock.expect_call().will_once(Return(123))
            assert next(gen) == 123

        def test_adapt_with_args(self, injector_stub: SupportsInject, generic_mock):

            def make_object(foo: int, bar: float, baz: str):
                yield generic_mock(foo, bar, baz)

            adapted = adapt_func_for_auto_mode(make_object)
            assert inspect.isgeneratorfunction(adapted)
            gen = adapted(injector_stub)
            generic_mock.injector.inject.expect_call(int).will_once(Return(123))
            generic_mock.injector.inject.expect_call(float).will_once(Return(3.14))
            generic_mock.injector.inject.expect_call(str).will_once(Return("spam"))
            generic_mock.expect_call(123, 3.14, "spam").will_once(Return(123))
            assert next(gen) == 123

    class TestFunction:
        def test_adapt_with_no_args(self, injector_stub: SupportsInject, generic_mock):

            def make_object():
                return generic_mock()

            adapted = adapt_func_for_auto_mode(make_object)
            assert inspect.isfunction(adapted)
            generic_mock.expect_call().will_once(Return(123))
            assert adapted(injector_stub) == 123

        def test_adapt_with_args(self, injector_stub: SupportsInject, generic_mock):

            def make_object(foo: int, bar: float, baz: str):
                return generic_mock(foo, bar, baz)

            adapted = adapt_func_for_auto_mode(make_object)
            assert inspect.isfunction(adapted)
            generic_mock.injector.inject.expect_call(int).will_once(Return(123))
            generic_mock.injector.inject.expect_call(float).will_once(Return(3.14))
            generic_mock.injector.inject.expect_call(str).will_once(Return("spam"))
            generic_mock.expect_call(123, 3.14, "spam").will_once(Return(123))
            assert adapted(injector_stub) == 123
