from typing import Callable, Any


class KwargsFilter:
    """A helper to filter out keyword arguments according to given
    criteria.

    :param skip_if:
        A function taking keyword argument value and returning ``True`` if
        that value should be skipped (i.e. keyword arg won't be passed) or
        ``False`` otherwise.
    """


    def __init__(self, skip_if: Callable[[Any], bool]):
        self._skip_if = skip_if

    def apply(self, **kwargs):
        """Apply filter to given ``kwargs`` and return iterator to kwargs
        filtered according to given criteria."""
        return {
            k: v for k, v in kwargs.items()
            if not self._skip_if(v)
        }
