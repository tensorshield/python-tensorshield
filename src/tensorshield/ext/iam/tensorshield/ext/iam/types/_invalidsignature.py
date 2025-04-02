

class InvalidSignature(ValueError):

    def __repr__(self): # pragma: no cover
        return f'{type(self)}: {self.args[0]}'