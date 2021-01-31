import abc


class Base(Exception, abc.ABC):
    """Common base class for all PyDIo exceptions.

    You can use this class to catch all exceptions that this library may
    raise.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self._args = dict(kwargs)

    def __str__(self):
        return self.message_template.format(self=self)

    @property
    @abc.abstractmethod
    def message_template(self):
        pass

    @property
    def args(self):
        return self._args
