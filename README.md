![PyPI](https://img.shields.io/pypi/v/pydio)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydio)
![PyPI - License](https://img.shields.io/pypi/l/pydio)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pydio)
[![codecov](https://codecov.io/gh/mwiatrzyk/pydio/branch/master/graph/badge.svg?token=Y6DJDSOR6M)](https://codecov.io/gh/mwiatrzyk/pydio)

# PyDio

Simple and functional dependency injection toolkit for Python.

## About

PyDio aims to be simple, yet still powerful, allowing you to feed
dependencies inside your application in a flexible way. PyDio design is based
on simple assumption, that dependency injection can be achieved using simple
**key-to-function** map, where **key** specifies **type of object** you want
to inject and **function** is a **factory** function that creates
**instances** of that type.

In PyDio, this is implemented using **providers** and **injectors**. You use
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

You can install PyDio using one of following methods:

1) From PyPI (for stable releases):

    ```shell
    $ pip install PyDio
    ```

2) From test PyPI (for stable and development releases):

    ```shell
    $ pip install -i https://test.pypi.org/simple/ PyDio
    ```

3) Directly from source code repository (for all releases):

    ```shell
    $ pip install git+https://gitlab.com/zef1r/PyDio.git@[branch-or-tag]
    ```

## Documentation

You have two options available:

1) Visit [PyDio's ReadTheDocs](https://pydio.readthedocs.io/en/latest/) site.

2) Take a tour around [functional tests](https://github.com/mwiatrzyk/pydio/tree/master/tests/functional).

## License

This project is released under the terms of the MIT license.

See [LICENSE.txt](https://github.com/mwiatrzyk/pydio/blob/master/LICENSE.txt) for more details.

## Author

Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
