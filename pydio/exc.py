# ---------------------------------------------------------------------------
# pydio/exc.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import abc


class Base(Exception, abc.ABC):
    """Common base class for all PyDio exceptions.

    You can use this class to catch all exceptions that this library may
    raise.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self._params = dict(kwargs)

    def __str__(self):
        return self.message_template.format(self=self)

    @property
    @abc.abstractmethod
    def message_template(self) -> str:
        """Specify message template.

        This must be defined in subclass and provides template to render
        exception message. This template can use **self** to access exception
        data, for example::

            class MyException(Base):
                message_template = 'Failed: foo={self.foo!r}'
        """

    @property
    def params(self) -> dict:
        """Dictionary containing all keyword args given in constructor.

        In subclass, this can be used as source of data when adding another
        properties.
        """
        return self._params


class InjectorError(Base):
    """Base class for exceptions that can be raised by
    :class:`pydio.base.IInjector` instances."""


class ProviderError(Base):
    """Base class for exceptions that can be raised by
    :class:`pydio.base.IProvider` instances."""
