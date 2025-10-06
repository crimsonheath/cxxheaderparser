import typing

if typing.TYPE_CHECKING:
    from .lexer import LexToken, Location


class CxxParseError(Exception):
    """
    Exception raised when a parsing error occurs
    """

    def __init__(self, msg: str, tok: typing.Optional["LexToken"] = None, location: typing.Optional["Location"] = None) -> None:
        Exception.__init__(self, msg)
        self.tok = tok
        self.location = location
