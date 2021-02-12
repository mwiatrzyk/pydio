.. ----------------------------------------------------------------------------
.. docs/source/quickstart.rst
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

    class InMemoryTodoStorage(ITodoItemStorage):

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
            self._todo_storage = InMemoryTodoStorage()

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
            self._db_name = db_name

        def connect(self):
            connection = sqlite3.connect(self._db_name)
            c = connection.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS todos (
                uuid UUID PRIMARY KEY,
                created DATETIME,
                title TEXT,
                description TEXT,
                done BOOLEAN)""")
            connection.commit()
            return connection

    class SQLiteTodoStorage(ITodoItemStorage):

        def __init__(self, connection):
            self._conn = connection

        def create(self, item):
            c = self._conn.cursor()
            c.execute(
                "INSERT INTO todos VALUES (?, ?, ?, ?, ?)",
                [str(item.uuid), item.created, item.title, item.description,
                item.done])

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
                self._todo_storage = SQLiteTodoStorage(self._database.connect())
            else:
                self._todo_storage = InMemoryTodoStorage()

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

Introducing providers
---------------------

As you can see, when implementing additional storages, our business logic was
not affected at all, however configuration part of our application was
getting more complicated. Now let's do some refactoring with PyDio.

First, we need to create **providers**. Providers are used to wrap
user-defined factory functions and give it a key that can be referenced
later. Here are providers for our two previously created storages:

.. testcode::

    from pydio.api import Provider

    provider = Provider()

    @provider.provides(ITodoItemStorage)
    def make_in_memory_todo_storage():  # (1)
        return InMemoryTodoStorage()

    @provider.provides(ITodoItemStorage, env='production')
    def make_sqlite_todo_storage():  # (2)
        database = SQLiteDatabase(':memory:')
        return SQLiteTodoStorage(database.connect())

We have created two object factories with a key set in both to
**ITodoItemStorage** - our interface created earlier. Object factory (1) will
be used as a default for that key, while (2) will only be used for production
environment. Of course, environment names are not predefined - you can set it
to anything you like. The only requirement is to use same name later.

Introducing injectors
---------------------

Now let me introduce second element of PyDio library - the **injector**.
Here's our TODO application from earlier example refactored to use injector:

.. testcode::

    from pydio.api import Injector  # (1)

    class TodoApplication:

        def __init__(self, env):
            self._injector = Injector(provider, env=env)  # (2)

        @property
        def _todo_storage(self):
            return self._injector.inject(ITodoItemStorage)  # (3)

        def create(self, title: str, description: str):
            CreateTodo(self._todo_storage).invoke(title, description)

        def complete(self, item_uuid: uuid.UUID):
            CompleteTodo(self._todo_storage).invoke(item_uuid)

        def list(self) -> List[dict]:
            return [x for x in ListTodos(self._todo_storage).invoke()]

        def delete(self, item_uuid: uuid.UUID):
            DeleteTodo(self._todo_storage).invoke(item_uuid)

.. doctest::
    :hide:

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

And now a brief explanation:

    * First, we need to import :class:`pydio.injector.Injector` class (1)

    * Now we have to create instance of that class. We need to pass
      provider created earlier and environment given from the outside (2).
      Our newly created injector will later use given provider and
      environment to find matching factory.

    * And finally (3), we use :meth:`pydio.injector.Injector.inject` method to
      perform injections. We use same key as previously in provider, and
      environment passed in constructor will be used implicitly to find
      matching variant of our factory.

As you can see, the code of our application is much simpler after
refactoring. Moreover, we can easily attach another implementation of our
storage - we just need to create another factory, and decorate it with same
key, but different environment. Here's an example that uses mock this time:

.. testcode::

    from mockify.mock import ABCMock

    @provider.provides(ITodoItemStorage, env='testing')
    def make_storage_mock():
        return ABCMock('storage_mock', ITodoItemStorage)

And now, let's run our **unchanged** application code, but giving it an
environment we've just used:

.. doctest::

    >>> app = TodoApplication('testing')
    >>> app.create('shopping', 'buy some milk')
    Traceback (most recent call last):
        ...
    mockify.exc.UninterestedCall: No expectations recorded for mock:
    <BLANKLINE>
    at <doctest default[0]>:13
    --------------------------
    Called:
      storage_mock.create(<TodoItem object at ...>)

As you can see, our mock was now triggered - not in-memory, neither SQLite
storage.

.. note::
    The call failed with exception, because we did not record any
    expectations - that's default behaviour for Mockify. Please proceed to
    https://mockify.readthedocs.io/en/latest/ if you want to read more about
    Mockify - my other project.

Using nested injections
-----------------------

Our example is rather trivial. In real life projects there are often much
more dependencies to be injected, and sometimes it is event necessary to
inject dependencies to the object that is being injected as well (nested
injections). To show how this works, let's first extract our use case class
constructors out of the application and use provider to provide those as
well. Of course, our use cases will still need a storage, so we will have to
use nested injections:

.. testcode::

    provider = Provider()

    @provider.provides(ITodoItemStorage)
    def make_in_memory_todo_storage():
        return InMemoryTodoStorage()

    @provider.provides(ITodoItemStorage, env='testing')
    def make_storage_mock():
        return ABCMock('storage_mock', ITodoItemStorage)

    @provider.provides(ITodoItemStorage, env='production')
    def make_sqlite_todo_storage():
        database = SQLiteDatabase(':memory:')
        return SQLiteTodoStorage(database.connect())

    @provider.provides(CreateTodo)
    def make_create_todo(injector: Injector): # (1)
        return CreateTodo(injector.inject(ITodoItemStorage))  # (2)

    @provider.provides(CompleteTodo)
    def make_complete_todo(injector: Injector):
        return CompleteTodo(injector.inject(ITodoItemStorage))

    @provider.provides(ListTodos)
    def make_list_todos(injector: Injector):
        return ListTodos(injector.inject(ITodoItemStorage))

    @provider.provides(DeleteTodo)
    def make_delete_todos(injector: Injector):
        return DeleteTodo(injector.inject(ITodoItemStorage))

And now some explanation:

    * First, we need to add argument for passing current injector to our
      factory function. All supported arguments are:

        * **injector** - for passing current injector (the one that owns that
          object factory)

        * **key** - for passing key assigned to that factory (**CreateTodo** in
          this case)

        * **env** - for passing environment name

      These names are reserved currently, however the order may be changed -
      you can pick from 0-3 arguments out of that predefined ones depending
      on your needs. In other words, this works similarly to PyTest's
      fixtures.

    * And finally (2), we use **injector** just like in our application class
      earlier.

Okay, we have our provider configured, so let's now rewrite our application
again. This time we'll use injector to inject use case classes only:

.. testcode::

    class TodoApplication:

        def __init__(self, env):
            self._injector = Injector(provider, env=env)

        def create(self, title: str, description: str):
            self._injector.inject(CreateTodo).invoke(title, description)

        def complete(self, item_uuid: uuid.UUID):
            self._injector.inject(CompleteTodo).invoke(item_uuid)

        def list(self) -> List[dict]:
            return [x for x in self._injector.inject(ListTodos).invoke()]

        def delete(self, item_uuid: uuid.UUID):
            self._injector.inject(DeleteTodo).invoke(item_uuid)

.. doctest::
    :hide:

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

Using scopes
------------

The solution we've prepared so far would not work in real situations unless
we create different application object for every action. That is due to the
fact, that each object factory is **called only once** per injector's
lifetime. And since we create injector in application's constructor, we would
have to call it (the constructor) again for every method call - otherwise we
would start sharing our objects between API calls, and that may not be
expected behavior.

To solve this issue, PyDio provides **scopes**. Scopes are implemented by
creating new injector from given one, and giving the new one access to
user-defined scope, plus its ancestors. Such created injectors can have
shorter lifetime than the root one.

But we also need to set scopes when factory functions are registered to
provider - just like we did for environments:

.. testcode::

    provider = Provider()

    @provider.provides(ITodoItemStorage, scope='app')
    def make_in_memory_todo_storage():
        return InMemoryTodoStorage()

    @provider.provides(ITodoItemStorage, env='testing', scope='app')
    def make_storage_mock():
        return ABCMock('storage_mock', ITodoItemStorage)

    @provider.provides(ITodoItemStorage, env='production', scope='app')
    def make_sqlite_todo_storage():
        database = SQLiteDatabase(':memory:')
        return SQLiteTodoStorage(database.connect())

    @provider.provides(CreateTodo, scope='action')
    def make_create_todo(injector: Injector):
        return CreateTodo(injector.inject(ITodoItemStorage))

    @provider.provides(CompleteTodo, scope='action')
    def make_complete_todo(injector: Injector):
        return CompleteTodo(injector.inject(ITodoItemStorage))

    @provider.provides(ListTodos, scope='action')
    def make_list_todos(injector: Injector):
        return ListTodos(injector.inject(ITodoItemStorage))

    @provider.provides(DeleteTodo, scope='action')
    def make_delete_todos(injector: Injector):
        return DeleteTodo(injector.inject(ITodoItemStorage))

We've registered our factories using two scopes: *app* and *action*. Now,
let's change our application class to something like this:

.. testcode::

    injector = Injector(provider)  # (1)

    class TodoApplication:

        def __init__(self, env):
            self._injector = injector.scoped('app', env=env)  # (2)

        def create(self, title: str, description: str):
            with self._injector.scoped('action') as injector:  # (3)
                injector.inject(CreateTodo).invoke(title, description)

        def complete(self, item_uuid: uuid.UUID):
            with self._injector.scoped('action') as injector:
                injector.inject(CompleteTodo).invoke(item_uuid)

        def list(self) -> List[dict]:
            with self._injector.scoped('action') as injector:
                return [x for x in injector.inject(ListTodos).invoke()]

        def delete(self, item_uuid: uuid.UUID):
            with self._injector.scoped('action') as injector:
                injector.inject(DeleteTodo).invoke(item_uuid)

        def shutdown(self):
            self._injector.close()

.. doctest::
    :hide:

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
    >>> app.shutdown()

And now some explanation:

    * We've created a root injector at (1)

    * Then, in our application, we've created a **scoped** injector from our
      root and named it *app* - it will be application-wide. This injector
      will be able to use object factories:

        * that does not have scope assigned,
        * that has *app* scope assigned.

      All other will not be accessible from there.

    * Finally, in our actions we've created another scoped injector, from our
      application's one, and named it with a scope *action* (3). This injector
      will be able to use object factories:

        * that does not have scope assigned,
        * that have *app* scope assigned (as it is a child of *app* scoped injector),
        * that have *action* scope assigned.

      And - like previously - all other will not be accessible.

    * The lifetime of each injector is:

        * Same as for process (root injector)
        * Until ``shutdown()`` is called (*app* injector)
        * Until we are under context manager (each *action* injector)

Using generator-based object factories
--------------------------------------

We are still missing one important thing in our application - database
sessions. Of course, that is not needed for a in-memory storage, but
definitely will have to be used for SQL-based storage. And the session scope
should be limited only to actions. How to do that using PyDio? Here's a
solution:

.. testcode::

    provider = Provider()

    @provider.provides('database', env='production', scope='app')  # (1)
    def make_database():
        return SQLiteDatabase(':memory:').connect()

    @provider.provides(ITodoItemStorage, env='production', scope='action')
    def make_sqlite_todo_storage(injector):
        connection = injector.inject('database')  # (2)
        try:
            yield SQLiteTodoStorage(connection)  # (3)
        except Exception:
            connection.close()
        else:
            connection.commit()

.. testcode::
    :hide:

    @provider.provides(ITodoItemStorage, scope='app')
    def make_in_memory_todo_storage():
        return InMemoryTodoStorage()

    @provider.provides(ITodoItemStorage, env='testing', scope='app')
    def make_storage_mock():
        return ABCMock('storage_mock', ITodoItemStorage)

    @provider.provides(CreateTodo, scope='action')
    def make_create_todo(injector: Injector):
        return CreateTodo(injector.inject(ITodoItemStorage))

    @provider.provides(CompleteTodo, scope='action')
    def make_complete_todo(injector: Injector):
        return CompleteTodo(injector.inject(ITodoItemStorage))

    @provider.provides(ListTodos, scope='action')
    def make_list_todos(injector: Injector):
        return ListTodos(injector.inject(ITodoItemStorage))

    @provider.provides(DeleteTodo, scope='action')
    def make_delete_todos(injector: Injector):
        return DeleteTodo(injector.inject(ITodoItemStorage))

This time, we've extracted making database to a separate factory function (1)
and changed the scope for ``make_sqlite_todo_storage`` function to *action*.
Notice, that the scope of ``make_database`` function is still set to *app*,
so database object will be bound to *app* injector and reused by all *action*
injectors. There is one more important thing: we've used a **generator** in
(3). Thanks to this, we were able to customize cleanup behavior for that
particular factory to either do a commit, or a rollback - in similar way as
in PyTest fixtures.

That will work with unchanged application code from previous example.

.. testcode::
    :hide:

    injector = Injector(provider)

    class TodoApplication:

        def __init__(self, env):
            self._injector = injector.scoped('app', env=env)

        def create(self, title: str, description: str):
            with self._injector.scoped('action') as injector:
                injector.inject(CreateTodo).invoke(title, description)

        def complete(self, item_uuid: uuid.UUID):
            with self._injector.scoped('action') as injector:
                injector.inject(CompleteTodo).invoke(item_uuid)

        def list(self) -> List[dict]:
            with self._injector.scoped('action') as injector:
                return [x for x in injector.inject(ListTodos).invoke()]

        def delete(self, item_uuid: uuid.UUID):
            with self._injector.scoped('action') as injector:
                injector.inject(DeleteTodo).invoke(item_uuid)

        def shutdown(self):
            self._injector.close()

.. doctest::
    :hide:

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
    >>> app.shutdown()
