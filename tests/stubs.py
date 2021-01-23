import abc


class IDatabase(abc.ABC):
    pass


class IAction(abc.ABC):
    pass


class SQLiteDatabase(IDatabase):
    pass


class DummyAction(IAction):

    def __init__(self, database: IDatabase):
        self.database = database
