"""HTTP/SSE transport for Remote Terminal MCP Server."""

import asyncio
import os
from typing import Any

import mcp.server.sse
import uvicorn
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, Mount

from .server import (
    server,
    handle_call_tool,
    handle_list_resources,
    handle_read_resource,
    handle_list_tools,
)

# Create SSE transport
sse_transport = SseServerTransport("/messages/")


async def handle_sse(request: Request) -> Response:
    """Handle incoming SSE connections."""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name="remote-terminal",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
    # Return empty response to avoid NoneType error
    return Response()


# Create Starlette routes
routes = [
    Route("/sse", endpoint=handle_sse, methods=["GET"]),
    Mount("/messages/", app=sse_transport.handle_post_message),
]

# Create Starlette application
app = Starlette(routes=routes)


def run_main(
    host: str = "0.0.0.0",
    port: int = 8080,
    log_level: str = "info",
) -> None:
    """Run the HTTP/SSE server.

    Args:
        host: Host to bind to (default: 0.0.0.0 for all interfaces)
        port: Port to bind to (default: 8080)
        log_level: Log level (default: info)
    """
    # Allow overriding via environment variables
    host = os.getenv("MCP_HOST", host)
    port = int(os.getenv("MCP_PORT", port))
    log_level = os.getenv("MCP_LOG_LEVEL", log_level)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Remote Terminal MCP Server with HTTP/SSE transport"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Log level (default: info)",
    )

    args = parser.parse_args()

    run_main(
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )
