from .base import IProvider, IInjector


class Injector(IInjector):

    def __init__(self, provider: IProvider):
        self._provider = provider
        self._cache = {}

    def inject(self, key):
        if key in self._cache:
            return self._cache[key].target
        unbound_instance = self._provider.get(key)
        if unbound_instance is None:
            raise self.NoProviderFound(key=key)
        instance = unbound_instance.bind(self)
        self._cache[key] = instance
        return instance.target
