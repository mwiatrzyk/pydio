"""A backport module containing upcoming v1 release of PyDIO library.

This module contains classes and types that are candidate version of the
upcoming 1.0.0 release of PyDIO library. During past 2-3 years of intensive use
of this library I have found some gaps worth fixing, and some other worth
implementing in a different way. And since these changes required a lot of
backwards incompatible changes I have decided to go with a special ``v1``
submodule that can be safely released along with the current layout, with an
easy way to adapt imports once a final v1 release is made.

Here is a short list of most important changes:

**Interfaces based on Protocols, not ABCs**

    All interfaces are now based on :class:`typing.Protocol` as a base and structural
    typing.

    All new interfaces are available via :mod:`pydio.v1.interface` module.

**Explicit async and non-async support**

    So far, PyDIO used a hybrid way of supporting async and non-async code, by
    returning either ``T``, or ``Awaitable[T]`` (depending on what provider was
    used to provide a value). That worked, but a drawback was a bit messy
    implementation on the library side, and problematic typing on the user
    side:

    .. testcode::

        from pydio.api import Provider, Injector

        provider = Provider()

        @provider.provides(int)
        def make_int():
            return 123

        @provider.provides(float)
        async def make_float():
            return 3.14

        injector = Injector(provider)

        async def client():
            int_val = injector.inject(int)  # without `await`
            float_val = await injector.inject(float)  # with `await`
            print(int_val, float_val)  # would print: 123 3.14

    Now you have to use either :class:`pydio.v1.injectors.Injector` (for
    non-async code), or :class:`pydio.v1.injectors.AsyncInjector` (for async
    code):

    .. testcode::

        from pydio.v1.api import Provider, Injector, AsyncInjector, provides

        provider = Provider()

        @provides(provider, int)
        def make_int():
            return 123

        @provides(provider, float)
        async def make_float():
            return 3.14

        async def async_client():
            injector = AsyncInjector(provider)
            int_val = await injector.inject(int)
            float_val = await injector.inject(float)
            print(int_val, float_val)  # would print: 123 3.14

        def client():
            injector = Injector(provider)
            int_val = injector.inject(int)
            # float_val = injector.inject(float) <- forbidden for non-async injector; this will fail (you have to remove `async` from provided factory)
            print(int_val)  # would print: 123

**Support for Annotated**

    Since upcoming 1.0.0 version there will be no more
    :class:`pydio.keys.Variant` type; it will be completely removed in favor of
    using :obj:`typing.Annotated`. Here's a basic usage:

    .. testcode::

        from typing import Annotated

        from pydio.v1.api import Provider, Injector, provides, inject_annotated

        PortType = Annotated[int, "port"]
        HostType = Annotated[str, "host"]

        provider = Provider()

        @provides(provider, PortType)
        def make_port():
            return 443

        @provides(provider, HostType)
        def make_host():
            return "localhost"

        def client():
            injector = Injector(provider)
            host = inject_annotated(injector, str, "host")  # or: injector.inject(HostType)
            port = inject_annotated(injector, int, "port")  # or: injector.inject(PortType)
            print(f"{host}:{port}")  # would print: localhost:443

**Automatic injection of dependencies**

    This is the most awaited feature.

    Since 1.0.0, PyDIO allows to use automatic dependency injection based on
    type hints. To use automated injection, you have to set ``auto`` mode for
    your resource factories and define their dependencies using arguments and
    type hints:

    .. testcode::

        from typing import Annotated

        from pydio.v1.api import Provider, Injector, provides, inject_annotated

        PortType = Annotated[int, "port"]
        HostType = Annotated[str, "host"]

        provider = Provider()

        @provides(provider, PortType)
        def make_port():
            return 443

        @provides(provider, HostType)
        def make_host():
            return "localhost"

        @provides(provider, tuple, mode="auto")
        def make_host_port(host: HostType, port: PortType):  # name is up to you, hint must be a type for which provider is set
            return (host, port)

        def client():
            injector = Injector(provider)
            host, port = injector.inject(tuple)
            print(host, port)  # would print: localhost 443

**Better scoping**

    Since version 1.0.0 PyDIO is using tuple of strings for naming scopes, not
    just a plain string. This allows to define scopes as trees (like namespaces
    in C++), not as a set of unrelated names.
"""
