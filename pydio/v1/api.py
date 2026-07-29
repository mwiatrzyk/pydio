"""A proxy module to access all public classes and functions.

It allows imports like this::

    from pydio.v1.api import Injector, Provider
"""

from .decorators import __all__ as _decorators_all
from .exc import __all__ as _exc_all
from .helpers import __all__ as _helpers_all
from .injectors import __all__ as _injectors_all
from .interface import __all__ as _interface_all
from .providers import __all__ as _providers_all

from .decorators import *
from .exc import *
from .helpers import *
from .injectors import *
from .interface import *
from .providers import *

__all__ = (
    *_decorators_all,
    *_exc_all,
    *_helpers_all,
    *_injectors_all,
    *_interface_all,
    *_providers_all
)  # type: ignore
