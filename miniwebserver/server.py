import os
import re
import gc
import sys
import asyncio

from miniwebserver.config import TYPE_CHECKING
from miniwebserver.utils import get_media_types, print_exception
from miniwebserver.enums import Header, MIMEType, Code, FILE_MARKER, Method
from miniwebserver.http import Request, Response

if TYPE_CHECKING:
    from typing import Any, Callable


BRACKETS = re.compile("[{}]")


class WebServer:
    def __init__(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 80,
        source_folder: str = ".",
        **globals: "Any",
    ):
        self.host: str = host
        self.port: int = port
        self.source_folder: str = source_folder
        self.globals: dict[str, "Any"] = globals

        self.routes: dict[
            Method,
            dict[tuple[tuple[str, ...], ...], Callable[..., Response]],
        ] = {}

    @staticmethod
    def _parse_path(path: str) -> tuple[tuple[str, ...], ...]:
        path = "/" if path == "/" else path.rstrip("/")

        return tuple(
            tuple(BRACKETS.sub("?", part).split("?")) for part in path.split("/")
        )

    @staticmethod
    def _make_safe_callback(
        callback: Callable[..., str | bytes], mime_type: MIMEType
    ) -> Callable[..., Response]:
        def inner(*args: "Any") -> Response:
            try:
                body = callback(*args)
                if isinstance(body, str):
                    body = body.encode()

                if isinstance(body, Response):
                    return body
                return Response.OK(body, mime_type)

            except Exception as err:
                return Response.InternalServerError(print_exception(err), MIMEType.html)

        return inner

    def _register_method(
        self, method: Method, path: str, mime_type: MIMEType
    ) -> Callable[[Callable[..., str]], None]:
        def inner(callback: Callable[..., str]) -> None:
            self.routes.setdefault(method, {})[self._parse_path(path)] = (
                self._make_safe_callback(callback, mime_type)
            )

        return inner

    def get(
        self, path: str, mime_type: MIMEType = MIMEType.html
    ) -> Callable[[Callable[..., str]], None]:
        return self._register_method(Method.GET, path, mime_type)

    def post(
        self, path: str, mime_type: MIMEType = MIMEType.NONE
    ) -> Callable[[Callable[[Request], str]], None]:
        return self._register_method(Method.POST, path, mime_type)

    def put(
        self, path: str, mime_type: MIMEType = MIMEType.NONE
    ) -> Callable[[Callable[..., str]], None]:
        return self._register_method(Method.PUT, path, mime_type)

    def delete(
        self, path: str, mime_type: MIMEType = MIMEType.NONE
    ) -> Callable[[Callable[..., str]], None]:
        return self._register_method(Method.DELETE, path, mime_type)

    def patch(
        self, path: str, mime_type: MIMEType = MIMEType.NONE
    ) -> Callable[[Callable[..., str]], None]:
        return self._register_method(Method.PATCH, path, mime_type)

    @staticmethod
    def _match_one_route(
        route: tuple[tuple[str, ...], ...], req_route: list[str]
    ) -> tuple[bool, tuple[str, ...]]:
        args: tuple[str, ...] = ()

        if len(route) != len(req_route):
            return False, ()

        for part, req_part in zip(route, req_route):
            if len(part) == 1 and part[0] == req_part:
                continue

            elif len(part) == 3:
                args = args + (req_part,)
                continue

            return False, ()

        return True, args

    def match_route(
        self, request: Request
    ) -> tuple[Callable[..., Response] | None, tuple[Any, ...]]:
        req_parts = request.path.split("/")

        for route in self.routes[request.method]:
            matched, args = self._match_one_route(route, req_parts)
            if matched:
                if request.method is not Method.GET:
                    args = (request,) + args
                return self.routes[request.method][route], args

        return None, ()

    def run(self) -> None:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self._handle_error)
        _ = loop.create_task(self.serve())

        try:
            loop.run_forever()

        except KeyboardInterrupt:
            pass

        finally:
            loop.close()

    async def _gc(self) -> None:
        _ = gc.collect()
        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
        await asyncio.sleep(1)

    async def serve(self) -> None:
        tcp_server = asyncio.start_server(
            self._handle_client, self.host, self.port, backlog=10
        )
        _ = asyncio.create_task(tcp_server)
        _ = asyncio.create_task(self._gc())

    def _handle_error(self, loop: asyncio.EventLoop, context: dict[str, Any]) -> None:
        _ = sys.print_exception(context.get("exception", RuntimeError("Unknown error")))

        loop.close()
        sys.exit()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        while True:
            request = await Request.get(reader)

            if request is None:
                writer.close()
                await writer.wait_closed()
                return

            callback, args = self.match_route(request)
            if callback is not None:
                response = callback(*args)

            elif request.method == Method.GET:
                try:
                    response = self.get_media(request)

                except Exception as err:
                    response = Response.InternalServerError(
                        print_exception(err), MIMEType.html
                    )

            elif request.method in (
                Method.POST,
                Method.PUT,
                Method.DELETE,
                Method.PATCH,
            ):
                response = Response.empty(Code.e404)

            else:
                response = Response.empty(Code.e405)

            try:
                await response.send(writer)

            except OSError:
                writer.close()
                await writer.wait_closed()
                return

    def _get_asset(
        self, requested_file_name: str, sub_t: str, extension: str
    ) -> bytes | None:
        if requested_file_name in os.listdir("{0}/assets".format(self.source_folder)):
            return b"%s%s/assets/%s" % (
                FILE_MARKER,
                self.source_folder,
                requested_file_name,
            )

        sub_t = extension if sub_t == "*" else sub_t
        if sub_t == "*":
            return None

        try:
            if requested_file_name in os.listdir(
                "%s/assets/%s" % (self.source_folder, sub_t)
            ):
                return b"%s%s/assets/%s/%s" % (
                    FILE_MARKER,
                    self.source_folder,
                    sub_t,
                    requested_file_name,
                )

        except OSError:
            pass

        return None

    def get_media(self, request: Request) -> Response:
        path = request.path
        requested_file_name = path[1:]

        split_index = path.rfind(".")
        extension = "" if split_index == -1 else path[(split_index + 1) :]
        mime_type = MIMEType.match(extension)

        if mime_type is None:
            return Response.empty(Code.e415)

        for accepted_type in get_media_types(
            request.headers.get(Header.Accept, b"*/*").decode()
        ):
            if MIMEType.is_asset(accepted_type):
                sub_t = accepted_type.split("/")[1]
                maybe_body = self._get_asset(requested_file_name, sub_t, extension)

                if maybe_body is None:
                    continue

                return Response.OK(maybe_body, mime_type)

            elif requested_file_name in os.listdir(self.source_folder):
                body = b"%s%s/%s" % (
                    FILE_MARKER,
                    self.source_folder,
                    requested_file_name,
                )
                return Response.OK(body, mime_type)

            else:
                continue

        return Response.empty(Code.e404)
