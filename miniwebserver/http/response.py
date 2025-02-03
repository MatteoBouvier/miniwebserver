import asyncio
import io
from micropython import const

from miniwebserver.http.version import Version
from miniwebserver.enums import FILE_MARKER, Code, Header, MIMEType

_WRITE_BUF_SIZE = const(2048)


class Response:
    def __init__(
        self,
        version: Version,
        status_code: Code,
        headers: dict[Header, bytes],
        body: bytes,
    ):
        self.version: Version = version
        self.status_code: Code = status_code
        self.headers: dict[Header, bytes] = headers
        self.body: bytes = body

    def __repr__(self) -> str:
        buf = io.StringIO(
            "Response <HTTP/{0}.{1} {2} {3}>\n".format(
                self.version.major,
                self.version.minor,
                Code.get_value(self.status_code),
                self.status_code,
            )
        )

        for header, value in self.headers.items():
            print("{0}: {1}".format(header, value), file=buf)

        print("(...)" if callable(self.body) else self.body, file=buf)
        r = buf.getvalue()
        buf.close()
        return r

    @classmethod
    def empty(cls, status_code: Code) -> "Response":
        return Response(Version(1, 1), status_code, {Header.ContentLength: b"0"}, b"")

    @classmethod
    def OK(cls, body: bytes, mime_type: MIMEType) -> "Response":
        headers: dict[Header, bytes] = {
            Header.TransferEncoding: Header.TransferEncodingV.Chunked,
            Header.Connection: Header.ConnectionV.KeepAlive,
        }

        if mime_type != MIMEType.NONE:
            headers[Header.ContentType] = mime_type  # pyright: ignore[reportArgumentType]

        return Response(
            Version(1, 1),
            Code.s200,
            headers,
            body,
        )

    @classmethod
    def InternalServerError(cls, body: bytes, mime_type: MIMEType) -> "Response":
        return Response(
            Version(1, 1),
            Code.e500,
            {
                Header.ContentType: mime_type,  # pyright: ignore[reportArgumentType]
                Header.ContentLength: b"%s" % len(body),
            },
            body,
        )

    async def send(self, writer: asyncio.StreamWriter) -> None:
        writer.write(
            b"HTTP/%d.%d %d %s\r\n"
            % (
                self.version.major,
                self.version.minor,
                Code.get_value(self.status_code),
                self.status_code,
            )
        )

        for header, value in self.headers.items():
            writer.write(b"%s: %s\r\n" % (header, value))

        writer.write(b"\r\n")
        await writer.drain()

        if len(self.body):
            if self.body.startswith(FILE_MARKER):
                data = open(self.body[6:], "rb")
            else:
                data = io.BytesIO(self.body)

            try:
                if (
                    self.headers.get(Header.TransferEncoding)
                    == Header.TransferEncodingV.Chunked
                ):
                    chunk = data.read(_WRITE_BUF_SIZE)
                    while chunk:
                        # Send the size of the chunk in hexadecimal, followed by the chunk itself
                        writer.write(b"%X\r\n" % len(chunk))
                        writer.write(chunk)
                        writer.write(b"\r\n")

                        chunk = data.read(_WRITE_BUF_SIZE)
                        await writer.drain()

                    writer.write(
                        b"0\r\n\r\n"
                    )  # Send the zero-length chunk to indicate end
                    await writer.drain()

                else:
                    # determine length from the Content-Length
                    assert self.headers.get(Header.ContentLength) is not None, (
                        "No Content-Length defined"
                    )
                    writer.write(data.read())
                    await writer.drain()

            finally:
                data.close()
