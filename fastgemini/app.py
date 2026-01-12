"""
Gemini Application - FastAPI-style server framework
"""

import asyncio
import logging
import ssl
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastgemini.enums import Status
from fastgemini.router import GeminiRouter, RouteHandler
from fastgemini.schema import GeminiRequest, GeminiResponse
from fastgemini.ssl import create_server_ssl_context

logger = logging.getLogger(__name__)

# Exception handler type
ExceptionHandler = Callable[
    [GeminiRequest, Exception],
    Awaitable[GeminiResponse],
]

# Middleware type
MiddlewareHandler = Callable[
    [GeminiRequest, RouteHandler],
    GeminiResponse,
]


class GeminiApp(GeminiRouter):
    """
    Main Gemini Application class.

    FastAPI-style framework for building Gemini protocol servers.

    Example:
        app = GeminiApp()

        @app.route("/")
        async def index(request: GeminiRequest) -> GeminiResponse:
            return GeminiResponse(
                status=Status.SUCCESS,
                body="# Welcome to Gemini!\\n",
            )

        if __name__ == "__main__":
            app.run()
    """

    def __init__(
        self,
        *,
        title: str = "FastGemini",
        version: str = "0.1.0",
        host: str = "localhost",
        port: int = 1965,
        certfile: Path,
        keyfile: Path,
        lifespan: Callable[["GeminiApp"], Any] | None = None,
        debug: bool = False,
    ) -> None:
        super().__init__()
        self.title = title
        self.version = version
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        self.debug = debug

        self._ssl_context: ssl.SSLContext | None = None
        self._exception_handlers: dict[type[Exception], ExceptionHandler] = {}
        # self._on_startup: list[Callable[[], Any]] = []
        # self._on_shutdown: list[Callable[[], Any]] = []
        self._lifespan = lifespan or _default_lifespan

    @property
    def ssl_context(self) -> ssl.SSLContext:
        """Lazily create SSL context."""
        if self._ssl_context is None:
            self._ssl_context = create_server_ssl_context(
                certfile=self.certfile,
                keyfile=self.keyfile,
            )
        return self._ssl_context

    def exception_handler(
        self,
        exc_class: type[Exception],
    ) -> Callable[[ExceptionHandler], ExceptionHandler]:
        """
        Register a custom exception handler.

        Example:
            @app.exception_handler(ValueError)
            async def handle_value_error(request, exc):
                return GeminiResponse(
                    status=Status.BAD_REQUEST,
                    content_type="Value error occurred",
                )
        """

        def decorator(handler: ExceptionHandler) -> ExceptionHandler:
            self._exception_handlers[exc_class] = handler
            return handler

        return decorator

    # def on_startup(self, func: Callable[[], Any]) -> Callable[[], Any]:
    #     """Register a startup event handler."""
    #     self._on_startup.append(func)
    #     return func

    # def on_shutdown(self, func: Callable[[], Any]) -> Callable[[], Any]:
    #     """Register a shutdown event handler."""
    #     self._on_shutdown.append(func)
    #     return func

    async def _handle_request(self, request: GeminiRequest) -> GeminiResponse:
        """
        Process a request and return a response.

        Handles routing, path parameter extraction, and error handling.
        """
        # Extract path from URL
        path = request.url.path or "/"

        # Find matching route
        match_result = self.match(path)

        if match_result is None:
            return GeminiResponse(
                status=Status.NOT_FOUND,
                content_type="Resource not found",
            )

        route, path_params = match_result

        # Store path params in request for handler access
        request.path_params = path_params  # type: ignore[attr-defined]

        try:
            response = await route.handler(request)
            return response
        except Exception as exc:
            return await self._handle_exception(request, exc)

    async def _handle_exception(
        self,
        request: GeminiRequest,
        exc: Exception,
    ) -> GeminiResponse:
        """Handle exceptions using registered handlers or default."""
        # Check for specific exception handler
        for exc_class, handler in self._exception_handlers.items():
            if isinstance(exc, exc_class):
                return await handler(request, exc)  # type: ignore[call-arg]

        # Default error response
        error_msg = f"{type(exc).__name__}: {exc}" if self.debug else "Internal server error"

        return GeminiResponse(
            status=Status.TEMPORARY_FAILURE,
            content_type=error_msg,
        )

    async def _connection_handler(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle a single Gemini connection."""
        try:
            # Get SSL object and peer certificate
            ssl_object = writer.get_extra_info("ssl_object")
            cert = ssl_object.getpeercert() if ssl_object else None

            # Get peer IP
            peername = writer.get_extra_info("peername")
            peer_ip = peername[0] if peername else None

            # Read request (max 1024 bytes + CRLF per Gemini spec)
            request_data = await reader.read(1026)

            # Parse request
            try:
                request = GeminiRequest(
                    url=request_data,
                    cert_data=cert,
                    peer_ip=peer_ip,
                )
            except Exception as e:
                response = GeminiResponse(
                    status=Status.BAD_REQUEST,
                    content_type=str(e),
                )
                writer.write(response.serialize().encode("utf-8"))
                await writer.drain()
                return

            # Handle request
            response = await self._handle_request(request)

            # Send response
            writer.write(response.serialize().encode("utf-8"))
            await writer.drain()

        except ConnectionResetError:
            # Client disconnected
            pass
        except Exception as e:
            if self.debug:
                logger.error(f"Connection error: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _serve(self) -> None:
        """Start the Gemini server."""
        logger.info(f"🚀 {self.title} v{self.version}")
        logger.info(f"   Gemini server running on gemini://{self.host}:{self.port}")

        async with self._lifespan(self):
            server = await asyncio.start_server(
                self._connection_handler,
                host=self.host,
                port=self.port,
                ssl=self.ssl_context,
            )
            async with server:
                await server.serve_forever()

    def run(self) -> None:
        """
        Run the Gemini server.

        This is a blocking call that starts the server.
        """
        asyncio.run(self._serve())

    async def serve(self) -> None:
        """
        Async version of run() for use within an existing asyncio context.
        """
        await self._serve()


@asynccontextmanager
async def _default_lifespan(app: GeminiApp):
    """Lifespan context manager for the GeminiApp."""

    try:
        yield
    finally:
        pass
