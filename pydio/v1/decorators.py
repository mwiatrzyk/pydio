from __future__ import annotations

from typing import Any, Callable, Literal


from . import _export_list, _adapters
from .interface import (
    T,
    AsyncFuncResult,
    FuncResult,
    EnvType,
    ScopeType,
    SupportsRegisterFactory,
)
from .helpers import register_func

__all__ = export = _export_list.ExportList()  # type: ignore


@export
def provides(
    provider: SupportsRegisterFactory,
    typ: type[T] | Any,
    *,
    scope: ScopeType = ScopeType(),
    env: EnvType = None,
    mode: Literal["manual", "passthrough", "auto"] = "manual",
):
    """Decorates provided user function as a resource factory.

    :param provider:
        The provider to use.

    :param typ:
        The type to register factory for.

    :param scope:
        The scope to register factory in.

    :param env:
        The environment to register factory for.

    :param mode:
        Configures how to pass injector to the decorated factory.

        Following values are available:

        - *manual* - allow to manually define what arguments the function will
          receive when called. The function will accept any combination
          (including empty) of the arguments from the following list:
          - *injector* - to pass injector
          - *typ* - to pass registered type
          - *scope* - to pass registered scope
          - *env* - to pass registered environment

        - *passthrough* - pass injector as is, require factory function to
          accept exactly one positional argument. This is the fastest possible
          way to call the factory as no runtime decisions are made.

          .. important::
                There are no sync vs async runtime checks when this mode is
                used.

        - *auto* - expect any arguments to be defined and require all to have
          annotations set. These annotations are then used to inject needed
          objects and call the function accordingly. This mode allows to inject
          based on annotations without touching injector directly.
    """

    def decorator(func: Callable[..., FuncResult[T] | AsyncFuncResult[T]]):
        if mode == "manual":
            register_func(
                provider,
                typ,
                _adapters.adapt_func_for_manual_mode(func, typ, scope=scope, env=env),
                scope=scope,
                env=env,
            )
        elif mode == "auto":
            register_func(provider, typ, _adapters.adapt_func_for_auto_mode(func), scope=scope, env=env)
        else:
            register_func(provider, typ, func, scope=scope, env=env)
        return func

    return decorator
