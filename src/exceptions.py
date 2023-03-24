class CombinatonException(Exception):
    pass


class NotUniqueSymbolsException(CombinatonException):
    pass


class TooManyRepeatsException(CombinatonException):
    pass


class UnknownModeException(CombinatonException):
    pass
