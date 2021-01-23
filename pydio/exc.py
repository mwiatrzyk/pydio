class Base(Exception):
    """Common base class for all PyDIo exceptions.

    You can use this class to catch all exceptions that this library may
    raise.
    """
    message_template = "unexpected error occured"

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        super().__init__(self.message_template.format(self=self))
