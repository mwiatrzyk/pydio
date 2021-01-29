import pytest

from pydio.provider import Provider


class _TestProvider:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.uut = Provider()

    def test_register_factory_function(self):

        def factory_func(injector):
            assert injector is self
            return 42

        self.uut.register_func('foo', factory_func)
        factory = self.uut.get('foo').bind(self)
        assert factory.get() == 42

    def test_register_generator_based_factory_function(self):

        def generator_based_factory_func(injector):
            assert injector is self
            yield 42

        self.uut.register_func('foo', generator_based_factory_func)
        factory = self.uut.get('foo').bind(self)
        assert factory.get() == 42
