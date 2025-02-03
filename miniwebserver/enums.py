from micropython import const
from miniwebserver.config import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union
    from enum import Enum
else:
    Enum = object


class MIMEType(Enum):
    NONE = const(b"*")
    html = const(b"text/html; charset=utf-8")
    css = const(b"text/css; charset=utf-8")
    js = const(b"text/javascript; charset=utf-8")
    json = const(b"application/json; charset=utf-8")
    ico = const(b"image/x-icon")

    @staticmethod
    def is_asset(typ: str) -> bool:
        t, sub_t = typ.split("/")

        return t in ("image", "*") or sub_t in ("css", "javascript")

    @classmethod
    def match(cls, extension: str) -> Union["MIMEType", None]:
        return {
            "": MIMEType.NONE,
            "html": MIMEType.html,
            "css": MIMEType.css,
            "js": MIMEType.js,
            "json": MIMEType.json,
            "ico": MIMEType.ico,
        }.get(extension)


FILE_MARKER: bytes = const(b"%FILE%")


class Method(Enum):
    GET = const(b"GET")
    POST = const(b"POST")
    PUT = const(b"PUT")
    DELETE = const(b"DELETE")
    PATCH = const(b"PATCH")

    @classmethod
    def match(cls, method: bytes) -> Union["Method", None]:
        return {
            b"GET": Method.GET,
            b"POST": Method.POST,
            b"PUT": Method.PUT,
            b"DELETE": Method.DELETE,
            b"PATCH": Method.PATCH,
        }.get(method)

    @staticmethod
    def all() -> tuple["Method", ...]:
        return (
            Method.GET,
            Method.POST,
            Method.PUT,
            Method.DELETE,
            Method.PATCH,
        )


class Header(Enum):
    Accept = const(b"Accept")
    Connection = const(b"Connection")

    class ConnectionV:
        KeepAlive: bytes = const(b"keep-alive")

    ContentType = const(b"Content-Type")
    ContentLength = const(b"Content-Length")
    TransferEncoding = const(b"Transfer-Encoding")

    class TransferEncodingV:
        Chunked: bytes = const(b"chunked")


class Code(Enum):
    i100 = const("Continue")
    i101 = const("Switching Protocols")
    i103 = const("Early Hints")
    s200 = const("OK")
    s201 = const("Created")
    s202 = const("Accepted")
    s203 = const("Non-Authoritative Information")
    s204 = const("No Content")
    s205 = const("Reset Content")
    s206 = const("Partial Content")
    r300 = const("Multiple Choices")
    r301 = const("Moved Permanently")
    r302 = const("Found")
    r303 = const("See Other")
    r304 = const("Not Modified")
    r307 = const("Temporary Redirect")
    r308 = const("Permanent Redirect")
    e400 = const("Bad Request")
    e401 = const("Unauthorized")
    e402 = const("Payment Required")
    e403 = const("Forbidden")
    e404 = const("Not Found")
    e405 = const("Method Not Allowed")
    e406 = const("Not Acceptable")
    e407 = const("Proxy Authentication Required")
    e408 = const("Request Timeout")
    e409 = const("Conflict")
    e410 = const("Gone")
    e411 = const("Length Required")
    e412 = const("Precondition Failed")
    e413 = const("Payload Too Large")
    e414 = const("URI Too Long")
    e415 = const("Unsupported Media Type")
    e416 = const("Range Not Satisfiable")
    e417 = const("Expectation Failed")
    e418 = const("I'm a teapot")
    e422 = const("Unprocessable Entity")
    e425 = const("Too Early")
    e426 = const("Upgrade Required")
    e428 = const("Precondition Required")
    e429 = const("Too Many Requests")
    e431 = const("Request Header Fields Too Large")
    e451 = const("Unavailable For Legal Reasons")
    e500 = const("Internal Server Error")
    e501 = const("Not Implemented")
    e502 = const("Bad Gateway")
    e503 = const("Service Unavailable")
    e504 = const("Gateway Timeout")
    e505 = const("HTTP Version Not Supported")
    e506 = const("Variant Also Negotiates")
    e507 = const("Insufficient Storage")
    e508 = const("Loop Detected")
    e510 = const("Not Extended")
    e511 = const("Network Authentication Required")

    @staticmethod
    def get_value(code: "Code") -> int:
        return {
            Code.i100: 100,
            Code.i101: 101,
            Code.i103: 103,
            Code.s200: 200,
            Code.s201: 201,
            Code.s202: 202,
            Code.s203: 203,
            Code.s204: 204,
            Code.s205: 205,
            Code.s206: 206,
            Code.r300: 300,
            Code.r301: 301,
            Code.r302: 302,
            Code.r303: 303,
            Code.r304: 304,
            Code.r307: 307,
            Code.r308: 308,
            Code.e400: 400,
            Code.e401: 401,
            Code.e402: 402,
            Code.e403: 403,
            Code.e404: 404,
            Code.e405: 405,
            Code.e406: 406,
            Code.e407: 407,
            Code.e408: 408,
            Code.e409: 409,
            Code.e410: 410,
            Code.e411: 411,
            Code.e412: 412,
            Code.e413: 413,
            Code.e414: 414,
            Code.e415: 415,
            Code.e416: 416,
            Code.e417: 417,
            Code.e418: 418,
            Code.e422: 422,
            Code.e425: 425,
            Code.e426: 426,
            Code.e428: 428,
            Code.e429: 429,
            Code.e431: 431,
            Code.e451: 451,
            Code.e500: 500,
            Code.e501: 501,
            Code.e502: 502,
            Code.e503: 503,
            Code.e504: 504,
            Code.e505: 505,
            Code.e506: 506,
            Code.e507: 507,
            Code.e508: 508,
            Code.e510: 510,
            Code.e511: 511,
        }[code]
