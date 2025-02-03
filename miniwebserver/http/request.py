import io
import json
import asyncio

from miniwebserver.config import TYPE_CHECKING
from miniwebserver.http.version import Version, get_version
from miniwebserver.enums import Header, Method

if TYPE_CHECKING:
    from typing import Any, Union


class Request:
    def __init__(
        self,
        method: Method,
        path: str,
        version: Version,
        headers: dict[Header, bytes],
        body: bytes = b"",
    ):
        self.method: Method = method
        self.path: str = path
        self.version: Version = version
        self.headers: dict[Header, bytes] = headers
        self.body: bytes = body

    def __repr__(self) -> str:
        buf = io.StringIO()
        print(
            "Request <{0} {1} HTTP/{2}.{3}>".format(
                self.method, self.path, self.version.major, self.version.minor
            ),
            file=buf,
        )

        for header, value in self.headers.items():
            print("\n{0}: {1}".format(header, value), file=buf)

        print("", file=buf)
        r = buf.getvalue()
        buf.close()
        return r

    @classmethod
    async def get(cls, reader: asyncio.StreamReader) -> Union["Request", None]:
        line = await reader.readline()

        if line == b"":
            return None

        method_, path, version = line.split()

        method = Method.match(method_)
        if method is None:
            return None

        path = path.decode()

        parsed_headers: dict[Header, bytes] = {}
        body = b""
        parsing_headers = True

        while True:
            line = await reader.readline()
            line = line.strip()
            if line:
                if parsing_headers:
                    name, value = line.split(b": ")
                    parsed_headers[name] = value  # pyright: ignore[reportArgumentType]

                else:
                    body += line

            elif parsing_headers:
                if not parsed_headers.get(Header.ContentLength, ""):
                    break
                parsing_headers = False

            else:
                break

        return Request(
            method,
            "/" if path == "/" else path.rstrip("/"),
            get_version(version),
            parsed_headers,
            body,
        )

    def json(self) -> dict[str, "Any"]:
        return json.loads(self.body)
