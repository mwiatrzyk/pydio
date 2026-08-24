"""The backend implementations for async Python libraries that can work with
PyDIO.

This module contains implementations of the
:class:`pydio.v1.interface.AsyncBackendLike` protocol that defines the API that
is required by PyDIO to work with async code.

Currently, only :mod:`pydio.v1.async_backends.asyncio` is available (and made
default), but there are plans to implement similar handler also for Trio.

Check :class:`pydio.v1.injectors.AsyncInjector` documentation to read more
about how to use these implementations.
"""
