import abc


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
