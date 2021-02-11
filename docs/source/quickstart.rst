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

Quickstart
==========

Introduction
------------

In this quickstart guide, we are going to write a simple TODO application
that allows:

    * creating items,
    * listing items,
    * marking items as completed,
    * deleting items

Application's business logic
----------------------------

First, we need a data class to represent our todo items. Let's then start by
creating a **TodoItem** entity:

.. testcode::

    import uuid
    from datetime import datetime

    class TodoItem:
        uid: uuid.UUID
        created: datetime
        title: str
        description: str
        done: bool = False

Now we need some kind of storage where our todo items will be stored. We will
do this formally, by designing interface. Of course we don't need it (it's a
Python), but interfaces are pretty useful with annotations. Here's our TODO
item storage interface:

.. testcode::

    import abc
    from typing import Iterable, Optional

    class ITodoItemStorage(abc.ABC):

        @abc.abstractmethod
        def create(self, item: TodoItem):
            pass

        @abc.abstractmethod
        def save(self, item: TodoItem):
            pass

        @abc.abstractmethod
        def get(self, item_uuid: uuid.UUID) -> Optional[TodoItem]:
            pass

        @abc.abstractmethod
        def delete(self, item_uuid: uuid.UUID):
            pass

        @abc.abstractmethod
        def list(self) -> Iterable[TodoItem]:
            pass

Finally, let's write our use case classes:

.. testcode::

    class CreateTodo:

        def __init__(self, todo_storage: ITodoItemStorage):
            self._todo_storage = todo_storage

        def invoke(self, title, description):
            item = TodoItem()
            item.uuid = uuid.uuid4()
            item.created = datetime.now()
            item.title = title
            item.description = description
            item.done = False
            self._todo_storage.create(item)

    class ListTodos:

        def __init__(self, todo_storage: ITodoItemStorage):
            self._todo_storage = todo_storage

        def invoke(self):
            for item in self._todo_storage.list():
                yield {  # we don't want to expose our entity
                    'uuid': item.uuid,
                    'created': item.created,
                    'title': item.title,
                    'description': item.description,
                    'done': item.done
                }

    class CompleteTodo:

        def __init__(self, todo_storage: ITodoItemStorage):
            self._todo_storage = todo_storage

        def invoke(self, item_uuid: uuid.UUID):
            item = self._todo_storage.get(item_uuid)
            if item is None:
                raise ValueError("invalid item uuid: {}".format(item_uuid))
            item.done = True
            self._todo_storage.save(item)

    class DeleteTodo:

        def __init__(self, todo_storage: ITodoItemStorage):
            self._todo_storage = todo_storage

        def invoke(self, item_uuid: uuid.UUID):
            self._todo_storage.delete(item_uuid)

And that's entire business logic of our simple TODO application. But so far,
we were only using a suite of unit tests, with **ITodoItemStorage** interface
mocked. Now, let's put some life into our application.

Application's API
-----------------

To make our business logic running we cannot use mocks any longer - now we
need a real implementation of **ITodoItemStorage** interface. Since we are
still doing development of our application, we still don't have to use any
SQL databases - just a simple in-memory store will do. Here's a very basic
implementation:

.. testcode::

    class InMemoryTodoRegistry(ITodoItemStorage):

        def __init__(self):
            self._todos = {}

        def create(self, item):
            self._todos[item.uuid] = item

        def save(self, item):
            self._todos[item.uuid] = item

        def delete(self, item_uuid):
            del self._todos[item_uuid]

        def get(self, item_uuid):
            return self._todos.get(item_uuid)

        def list(self):
            for item in self._todos.values():
                yield item

Now we can use it in our application. It will be represented by
**TodoApplication** class, with all use cases exposed as methods:

.. testcode::

    from typing import List

    class TodoApplication:

        def __init__(self):
            self._todo_storage = InMemoryTodoRegistry()

        def create(self, title: str, description: str):
            CreateTodo(self._todo_storage).invoke(title, description)

        def complete(self, item_uuid: uuid.UUID):
            CompleteTodo(self._todo_storage).invoke(item_uuid)

        def list(self) -> List[dict]:
            return [x for x in ListTodos(self._todo_storage).invoke()]

        def delete(self, item_uuid: uuid.UUID):
            DeleteTodo(self._todo_storage).invoke(item_uuid)

And here's how it works:

.. doctest::

    >>> app = TodoApplication()
    >>> app.create('shopping', 'buy some milk')
    >>> items = app.list()
    >>> items
    [{'uuid': ..., 'created': ..., 'title': 'shopping', 'description': 'buy some milk', 'done': False}]
    >>> app.complete(items[0]['uuid'])
    >>> app.list()
    [{'uuid': ..., 'created': ..., 'title': 'shopping', 'description': 'buy some milk', 'done': True}]
    >>> app.delete(items[0]['uuid'])
    >>> app.list()
    []

Adding another environment
--------------------------

Okay, so we have our basic scenario working in development environment. But
to make it work in production, we need some non-volatile storage. Therefore,
we need another implementation. Let it be a some kind of SQL database:

.. testcode::

    import sqlite3

    class SQLiteDatabase:

        def __init__(self, db_name):
            self._connection = sqlite3.connect(db_name)
            c = self._connection.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS todos (
                uuid UUID PRIMARY KEY,
                created DATETIME,
                title TEXT,
                description TEXT,
                done BOOLEAN)""")
            self._connection.commit()

        def connect(self):
            return self._connection

    class SQLiteTodoRegistry(ITodoItemStorage):

        def __init__(self, connection):
            self._conn = connection

        def create(self, item):
            c = self._conn.cursor()
            c.execute(
                "INSERT INTO todos VALUES (?, ?, ?, ?, ?)",
                [str(item.uuid), item.created, item.title, item.description,
                item.done])
            self._conn.commit()

        def save(self, item):
            c = self._conn.cursor()
            c.execute("UPDATE todos SET done=?", [item.done])  # Just for our case
            self._conn.commit()

        def delete(self, item_uuid):
            c = self._conn.cursor()
            c.execute("DELETE FROM todos WHERE uuid=?", [str(item_uuid)])

        def get(self, item_uuid):
            c = self._conn.cursor()
            c.execute("SELECT * FROM todos WHERE uuid=?", [str(item_uuid)])
            row = c.fetchone()
            return self._make_todo(row)

        def list(self):
            c = self._conn.cursor()
            c.execute("SELECT * FROM todos")
            for row in c.fetchmany():
                yield self._make_todo(row)

        def _make_todo(self, row):
            item = TodoItem()
            item.uuid = row[0]
            item.created = row[1]
            item.title = row[2]
            item.description = row[3]
            item.done = True if row[4] else False
            return item

And now, let's modify our original application. But this time, we need both
storages at once! We'll decide which one to use by giving environment name to
**TodoApplication**'s constructor:

.. testcode::

    from typing import List

    class TodoApplication:

        def __init__(self, env):
            if env == 'production':
                self._database = SQLiteDatabase(':memory:')
                self._todo_storage = SQLiteTodoRegistry(self._database.connect())
            else:
                self._todo_storage = InMemoryTodoRegistry()

        def create(self, title: str, description: str):
            CreateTodo(self._todo_storage).invoke(title, description)

        def complete(self, item_uuid: uuid.UUID):
            CompleteTodo(self._todo_storage).invoke(item_uuid)

        def list(self) -> List[dict]:
            return [x for x in ListTodos(self._todo_storage).invoke()]

        def delete(self, item_uuid: uuid.UUID):
            DeleteTodo(self._todo_storage).invoke(item_uuid)

As you can see, the code gets more complicated. And this is only one
interface with just only two implementations! Let's see how this works:

.. doctest::

    >>> app = TodoApplication('production')
    >>> app.create('shopping', 'buy some milk')
    >>> items = app.list()
    >>> items
    [{'uuid': ..., 'created': ..., 'title': 'shopping', 'description': 'buy some milk', 'done': False}]
    >>> app.complete(items[0]['uuid'])
    >>> app.list()
    [{'uuid': ..., 'created': ..., 'title': 'shopping', 'description': 'buy some milk', 'done': True}]
    >>> app.delete(items[0]['uuid'])
    >>> app.list()
    []
