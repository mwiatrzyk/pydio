import sys

_py_version = (sys.version_info.major, sys.version_info.minor)


if _py_version >= (3, 7):

    from contextlib import AbstractAsyncContextManager

else:  # Py36

    import abc

    class AbstractAsyncContextManager(abc.ABC):

        async def __aenter__(self):
            return self

        @abc.abstractmethod
        async def __aexit__(self, exc_type, exc, tb):
            pass
