# type: ignore

import sys

version = sys.version_info.major, sys.version_info.minor

if version < (3, 13):
    from .default import __all__ as _all
    from .default import *
else:
    from .py313 import __all__ as _all
    from .py313 import *

__all__ = (*_all,)  # type: ignore
