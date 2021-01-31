import abc


class Base(Exception, abc.ABC):
    """Common base class for all PyDio exceptions.

    You can use this class to catch all exceptions that this library may
    raise.

    This is an abstract base class; it requires :param:`message_template` to
    be declared in subclass.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self._args = dict(kwargs)

    def __str__(self):
        return self.message_template.format(self=self)

    @property
    @abc.abstractmethod
    def message_template(self) -> str:
        """Specify message template.

        You can use ``self`` in template to access exception's properties.
        """

    @property
    def args(self) -> dict:
        """Key-value pairs containing named parameters this exception was
        created with."""
        return self._args
