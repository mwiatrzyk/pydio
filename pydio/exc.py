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

    This is an abstract base class; it requires :param:`message_template` to
    be declared in subclass.
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

        You can use ``self`` in template to access exception's properties.
        """

    @property
    def params(self) -> dict:
        """Dictionary containing exception parameters given in
        constructor."""
        return self._params


class AlreadyClosedError(Base):
    message_template = "Underlying factory was already closed"


class InjectorError(Base):
    pass


class ProviderError(Base):
    pass
