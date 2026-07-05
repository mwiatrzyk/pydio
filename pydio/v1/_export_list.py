from typing import Optional, TypeVar

T = TypeVar("T")


class ExportList(list):
    """A helper for automated creation of ``__all__`` module level
    properties."""

    def __call__(self, func_or_cls: T) -> T:
        name: Optional[str] = getattr(func_or_cls, "__name__", None)
        if name is None:
            raise TypeError(f"cannot export {func_or_cls!r}; the '__name__' property is missing")
        self.append(name)
        return func_or_cls
