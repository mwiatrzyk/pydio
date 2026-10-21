![PyPI](https://img.shields.io/pypi/v/pydio)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydio)
![PyPI - License](https://img.shields.io/pypi/l/pydio)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pydio)
[![codecov](https://codecov.io/gh/mwiatrzyk/pydio/branch/master/graph/badge.svg?token=Y6DJDSOR6M)](https://codecov.io/gh/mwiatrzyk/pydio)

# PyDIO

Lightweight and functional dependency injection library for Python.

## Name

**PyDIO** (stylized as *PyDIO*, installable as `pydio`, pronounced
*"pie-dee-o"*) stands for **Python dependency injection library**.

## About

PyDIO aims to be simple, yet still powerful, allowing you to feed dependencies
inside your application in a flexible way. PyDIO design is based on simple
assumption that dependency injection can be achieved using a straightforward
**key-to-function** mapping, where **key** specifies **type of object** you
want to inject and **function** is a **factory** function that creates
**instances** of that type.

In PyDIO, this is implemented using **providers** and **injectors**. You use
providers to configure your **key-to-function** mapping, and then you use
injectors to perform a **lookup** of a specific key and creation of the final
object.

Here's a simple example:

```python
import abc

from pydio.api import Provider, Injector

provider = Provider()

@provider.provides('greet')
def make_greet():
    return 'Hello, world!'

def main():
    injector = Injector(provider)
    greet_message = injector.inject('greet')
    print(greet_message)

if __name__ == '__main__':
    main()
```

Now you can save the snippet from above as ``example.py`` file and execute
to see the output:

```shell
$ python example.py
Hello, world!
```

## Key features

* Support for any hashable keys: class objects, strings, ints etc.
* Support for any type of object factories: function, coroutine, generator,
  asynchronous generator.
* Automatic resource management via generator-based factories
  (similar to pytest's fixtures)
* Multiple environment support: testing, development, production etc.
* Limiting created object's lifetime to user-defined scopes: global,
  application, use-case etc.
* No singletons used, so there is no global state...
* ...but you still can create global injector on your own if you need it :-)

## Installation

You can install PyDIO using one of following methods:

1) From PyPI (for stable releases):

    ```shell
    $ pip install pydio
    ```

2) Directly from source code repository (for all releases):

    ```shell
    $ pip install git+https://github.com/mwiatrzyk/pydio.git@[branch-or-tag]
    ```

In addition to standard `pip` tool, you can also install it using `uv`,
`poetry` or other alternative.

## Documentation

You have two options available:

1) Visit [PyDIO's ReadTheDocs](https://pydio.readthedocs.io/en/latest/) site.

2) Take a tour around [functional tests](https://github.com/mwiatrzyk/pydio/tree/master/tests/functional).

## News

### PyDIO 1.x is coming...

Since version 0.5.2 there is a `pydio.v1` backport module available containing
candidate version of the upcoming 1.x PyDIO release. It is a result of library
refactoring with several improvements and few useful features added which are a
result of intensive use of this library in various projects. Some of these
changes include:

* Use of `typing.Protocol` instead of `abc.ABC` for interfaces

* Explicit async and non-async support via `pydio.v1.injectors.AsyncInjector`
  and `pydio.v1.injectors.Injector` classes.

* Support for `typing.Annotated` for custom variants of types (f.e.
  `Annotated[int, 'tcp.port']`)

* Automatic injections via type hints:

    ```python
    from pydio.v1.api import Provider, provides

    provider = Provider()

    @provides(provider, AbstractSomething, mode="auto")
    def build_something(foo: AbstractFoo, bar: AbstractBar):
        return Something(foo, bar)  # No manual injection needed
    ```

* Better scoping support via namespaces, not just plain string:

    Provider part:

    ```python
    from pydio.v1.api import Provider, provides

    provider = Provider()

    @provides(provider, AbstractSomething, scope=("parent", "child"), mode="auto")
    def build_something(foo: AbstractFoo, bar: AbstractBar):
        return Something(foo, bar)  # No manual injection needed
    ```

    Injection part:

    ```python
    from pydio.v1.api import Injector

    injector = Injector(provider)

    with injector.scoped("parent") as parent:
        with parent.scoped("child") as child:
            something = child.inject(AbstractSomething)
    ```

* Better type hinting support.

Visit [v1 API documentation](https://pydio.readthedocs.io/en/latest/api/pydio/v1.html) to read more.


## Disclaimer

**PyDIO** is an independent open-source project in the Python ecosystem. It
is not affiliated with, sponsored by, or endorsed by any company, organization,
or product of the same or similar name. Any similarity in names is purely
coincidental and does not imply any association.

## License

This project is released under the terms of the MIT license.

See [LICENSE.txt](https://github.com/mwiatrzyk/pydio/blob/master/LICENSE.txt) for more details.

## Author

Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
