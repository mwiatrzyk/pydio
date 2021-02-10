.. ----------------------------------------------------------------------------
.. docs/source/tutorial.rst
..
.. Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
..
.. This file is part of PyDio library documentation
.. and is released under the terms of the MIT license:
.. http://opensource.org/licenses/mit-license.php.
..
.. See LICENSE.txt for details.
.. ----------------------------------------------------------------------------

Tutorial
========

Introduction
------------

When you develop an application in accordance to SOLID principles, then most
likely you start by writing use cases at first, supported by dozens of
abstractions instead of final implementations. But that abstractions have to
be implemented at some point in time. And most likely, you will have to
implement at least 2 implementations for each: one for testing/development
purposes, and one for production use. When number of use cases grows, then
number of abstractions needed grows as well. That leads to more and more
complications in configuration part of application being developed. Finally,
you find yourself in a place, where some kind of tool is needed to manage
that part of application. And PyDio is one of such tools.

Begin writing a TODO application
--------------------------------

Let's assume we are writing a "todo" application that allows:

    * creating todos,
    * listing todos,
    * marking todos as completed,
    * deleting todos.

Since this is a todo application, it will work on some todo items. Single
todo item can be defined like this:

.. testcode::

    import uuid
    from datetime import datetime

    class TodoItem:
        uid: uuid.UUID
        created: datetime
        title: str
        description: str
        done: bool = False

This is a data class - a first business object in our application.

Now let's write first two use cases: one for creating items, and the other
for listing. Here's a final implementation - with all needed interfaces:

.. testcode::

    import abc
    import collections
    from typing import Iterable

    class ITodoWriter(abc.ABC):

        @abc.abstractmethod
        def save(self, item: TodoItem):
            pass

    class AddTodo:

        def __init__(self, todo_registry: ITodoWriter):
            self._todo_registry = todo_registry

        def invoke(self, title, description):
            item = TodoItem()
            item.uuid = uuid.uuid4()
            item.created = datetime.now()
            item.title = title
            item.description = description
            item.done = False
            self._todo_registry.save(item)

    class ITodoReader(abc.ABC):

        @abc.abstractmethod
        def list(self) -> Iterable[TodoItem]:
            pass

    class ListTodos:

        def __init__(self, todo_registry: ITodoReader):
            self._todo_registry = todo_registry

        def invoke(self):
            for item in self._todo_registry.list():
                yield {  # we don't want to expose our entity
                    'uuid': item.uuid,
                    'created': item.created,
                    'title': item.title,
                    'description': item.description,
                    'done': item.done
                }

So far, we were writing that classes with a help of unit tests, so our
**ITodoWriter** and **ITodoReader** interfaces were in fact mocked. But now we
want to use that classes inside our application:

.. testcode::

    class TodoApp:

        def create(self, title, description):
            todo_writer = None  # here we need an implementation
            handler = AddTodo(todo_writer)
            handler.invoke(title, description)

        def list(self):
            todo_reader = None  # here we need an implementation
            handler = ListTodos(todo_reader)
            return [x for x in handler.invoke()]

No we cannot use mocks any longer - we need a real implementation. Since we
are still doing development, we still don't have to use any SQL databases -
just a simple in-memory store will do. And since both use cases operate on
the same storage, we can make a single class that inherits from both
interfaces:

.. testcode::

    class InMemoryTodoRegistry(ITodoWriter, ITodoReader):

        def __init__(self):
            self._todos = []

        def save(self, item):
            self._todos.append(item)

        def list(self):
            yield from self._todos

Now we can use it in our application:

.. testcode::

    class TodoApp:

        def __init__(self):
            self._todo_registry = InMemoryTodoRegistry()

        def create(self, title, description):
            handler = AddTodo(self._todo_registry)
            handler.invoke(title, description)

        def list(self):
            handler = ListTodos(self._todo_registry)
            return [x for x in handler.invoke()]

And here's how it works:

.. doctest::

    >>> app = TodoApp()
    >>> app.create('shopping', 'buy some milk')
    >>> app.list()
    [{'uuid': ..., 'created': ..., 'title': 'shopping', 'description': 'buy some milk', 'done': False}]
