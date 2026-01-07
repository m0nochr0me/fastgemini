"""
Gemini Router - FastAPI-style route grouping
"""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from fastgemini.schema import GeminiRequest, GeminiResponse


# Type alias for route handlers
RouteHandler = Callable[["GeminiRequest"], Awaitable["GeminiResponse"]]


@dataclass
class Route:
    """Represents a single route with its handler and metadata."""

    path: str
    handler: RouteHandler
    name: str | None = None
    pattern: re.Pattern[str] = field(init=False)
    param_names: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Compile path pattern for matching."""
        self.pattern, self.param_names = self._compile_path(self.path)

    @staticmethod
    def _compile_path(
        path: str,
    ) -> tuple[re.Pattern[str], list[str]]:
        """
        Convert a path with parameters to a regex pattern.

        Supports:
        - Static paths: /hello/world
        - Path parameters: /user/{username}
        - Wildcards: /files/{path:path} (matches multiple segments)
        """
        param_names: list[str] = []
        pattern_parts: list[str] = []

        # Split path into segments
        segments = path.strip("/").split("/") if path != "/" else []

        for segment in segments:
            if segment.startswith("{") and segment.endswith("}"):
                # Path parameter
                param_spec = segment[1:-1]
                if ":" in param_spec:
                    param_name, param_type = param_spec.split(":", 1)
                    if param_type == "path":
                        # Wildcard - matches everything including slashes
                        pattern_parts.append(r"(?P<" + param_name + r">.+)")
                    else:
                        # Default: match single segment
                        pattern_parts.append(r"(?P<" + param_name + r">[^/]+)")
                else:
                    param_name = param_spec
                    pattern_parts.append(r"(?P<" + param_name + r">[^/]+)")
                param_names.append(param_name)
            else:
                # Static segment
                pattern_parts.append(re.escape(segment))

        # Build final pattern
        regex = "^/" + "/".join(pattern_parts) + "/?$" if pattern_parts else "^/$"

        return re.compile(regex), param_names

    def match(
        self,
        path: str,
    ) -> dict[str, str] | None:
        """
        Match a path against this route.

        Returns path parameters if matched, None otherwise.
        """
        match = self.pattern.match(path)
        if match:
            return match.groupdict()
        return None


class GeminiRouter:
    """
    Router for grouping Gemini routes.

    Similar to FastAPI's APIRouter, allows organizing routes
    into logical groups with optional prefix.

    Example:
        router = GeminiRouter(prefix="/api")

        @router.route("/users")
        async def list_users(request: GeminiRequest) -> GeminiResponse:
            ...
    """

    def __init__(self, prefix: str = "", name: str | None = None) -> None:
        self.prefix = prefix.rstrip("/")
        self.name = name
        self.routes: list[Route] = []

    def route(
        self,
        path: str,
        *,
        name: str | None = None,
    ) -> Callable[[RouteHandler], RouteHandler]:
        """
        Decorator to register a route handler.

        Args:
            path: The URL path pattern (e.g., "/hello", "/user/{id}")
            name: Optional name for the route

        Example:
            @router.route("/hello")
            async def hello(request: GeminiRequest) -> GeminiResponse:
                return GeminiResponse(status=Status.SUCCESS, body="Hello!")
        """

        def decorator(
            handler: RouteHandler,
        ) -> RouteHandler:
            full_path = self.prefix + path
            route = Route(
                path=full_path,
                handler=handler,
                name=name or handler.__name__,
            )
            self.routes.append(route)
            return handler

        return decorator

    def include_router(
        self,
        router: "GeminiRouter",
        *,
        prefix: str = "",
    ) -> None:
        """
        Include routes from another router.

        Args:
            router: The router to include
            prefix: Additional prefix for the included routes
        """
        for route in router.routes:
            new_path = self.prefix + prefix + route.path
            new_route = Route(
                path=new_path,
                handler=route.handler,
                name=route.name,
            )
            self.routes.append(new_route)

    def match(
        self,
        path: str,
    ) -> tuple[Route, dict[str, str]] | None:
        """
        Find a matching route for the given path.

        Returns (route, path_params) if found, None otherwise.
        """
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                return route, params
        return None
