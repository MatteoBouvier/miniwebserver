from miniwebserver.config import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import NamedTuple

    class Version(NamedTuple):
        major: int
        minor: int

else:
    from collections import namedtuple

    Version = namedtuple("Version", ("major", "minor"))


def get_version(v: bytes) -> Version:
    if not v.startswith(b"HTTP/"):
        raise ValueError

    M, m = v[5:].split(b".", 1)
    return Version(int(M), int(m))
