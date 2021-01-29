import abc


class IObject:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class IFoo(IObject):
    pass


class Foo(IFoo):
    pass


class IBar(IObject):
    pass


class Bar(IBar):
    pass


class Baz(IObject):
    pass


class IDatabase(abc.ABC):

    class IConnection(abc.ABC):
        @abc.abstractmethod
        def close(self):
            pass

    @abc.abstractmethod
    def connect(self) -> IConnection:
        pass


class IAction(abc.ABC):
    pass


class SQLiteDatabase(IDatabase):

    def connect(self):
        pass


class PostgresDatabase(IDatabase):

    class Connection(IDatabase.IConnection):

        def close(self):
            pass

    def connect(self):
        return self.Connection()


class DummyAction(IAction):

    def __init__(self, database: IDatabase):
        self.database = database
