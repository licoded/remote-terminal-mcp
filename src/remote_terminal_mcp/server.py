"""Remote Terminal MCP Server implementation."""

import asyncio
import json
import os
import shlex
import subprocess
from typing import Any

import mcp.server.stdio
from mcp import types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pydantic import BaseModel, Field, field_validator


class CommandExecutionResult(BaseModel):
    """Result of command execution."""

    return_code: int = Field(description="Process return code")
    stdout: str = Field(description="Standard output")
    stderr: str = Field(description="Standard error output")
    success: bool = Field(description="Whether command succeeded")


class ExecuteCommandInput(BaseModel):
    """Input schema for execute_command tool."""

    command: str = Field(
        description="Shell command to execute (will be parsed with shlex for safety)"
    )
    working_dir: str | None = Field(
        default=None,
        description="Working directory for command execution",
    )
    timeout: int = Field(
        default=30,
        description="Command timeout in seconds",
        ge=1,
        le=300,
    )
    env: dict[str, str] | None = Field(
        default=None,
        description="Environment variables for the command",
    )

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Validate command is not empty and doesn't contain obvious dangerous patterns."""
        v = v.strip()
        if not v:
            raise ValueError("Command cannot be empty")

        # Check for obviously dangerous command patterns
        dangerous_patterns = [
            "rm -rf /",
            "rm -rf /*",
            "mkfs",
            "dd if=/dev/zero",
            ":(){ :|:& };:",  # fork bomb
            "chmod -R 777 /",
        ]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Command contains dangerous pattern: {pattern}")

        return v


# Create the server instance
server = Server("remote-terminal")


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources."""
    return [
        types.Resource(
            uri="system://info",
            name="System Information",
            description="Get basic system information including platform, Python version, hostname",
            mimeType="application/json",
        ),
        types.Resource(
            uri="system://environment",
            name="Environment Variables",
            description="Get environment variables (sensitive values are redacted)",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri == "system://info":
        info = {
            "platform": os.platform(),
            "system": os.name,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "current_directory": os.getcwd(),
            "hostname": os.uname().nodename if hasattr(os, 'uname') else "unknown",
        }
        return json.dumps(info, indent=2)
    elif uri == "system://environment":
        # Filter out sensitive environment variables
        sensitive_keys = {
            "PASSWORD",
            "SECRET",
            "TOKEN",
            "API_KEY",
            "PRIVATE_KEY",
            "CREDENTIALS",
            "AUTH",
            "SESSION",
            "COOKIE",
        }

        env = {}
        for key, value in sorted(os.environ.items()):
            # Skip potentially sensitive variables
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                env[key] = "***REDACTED***"
            else:
                env[key] = value

        return json.dumps(env, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="execute_command",
            description="Execute a shell command on the remote system with safety validation and timeout protection",
            inputSchema=ExecuteCommandInput.model_json_schema(),
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls."""
    if name == "execute_command":
        # Validate and parse input
        try:
            input_data = ExecuteCommandInput(**arguments)
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Invalid input: {e}",
                )
            ]

        try:
            # Parse command safely using shlex
            args = shlex.split(input_data.command)

            # Prepare environment
            env = None
            if input_data.env:
                env = os.environ.copy()
                env.update(input_data.env)

            # Execute the command
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=input_data.working_dir or None,
                env=env,
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                result = CommandExecutionResult(
                    return_code=-1,
                    stdout="",
                    stderr=f"Command timed out after {input_data.timeout} seconds",
                    success=False,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result.model_dump_json(indent=2),
                    )
                ]

            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            result = CommandExecutionResult(
                return_code=process.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
                success=(process.returncode or 0) == 0,
            )

            return [
                types.TextContent(
                    type="text",
                    text=result.model_dump_json(indent=2),
                )
            ]

        except FileNotFoundError as e:
            result = CommandExecutionResult(
                return_code=127,
                stdout="",
                stderr=f"Command not found: {e}",
                success=False,
            )
            return [
                types.TextContent(
                    type="text",
                    text=result.model_dump_json(indent=2),
                )
            ]
        except PermissionError as e:
            result = CommandExecutionResult(
                return_code=126,
                stdout="",
                stderr=f"Permission denied: {e}",
                success=False,
            )
            return [
                types.TextContent(
                    type="text",
                    text=result.model_dump_json(indent=2),
                )
            ]
        except Exception as e:
            result = CommandExecutionResult(
                return_code=-1,
                stdout="",
                stderr=f"Error executing command: {e}",
                success=False,
            )
            return [
                types.TextContent(
                    type="text",
                    text=result.model_dump_json(indent=2),
                )
            ]
    else:
        raise ValueError(f"Unknown tool: {name}")


def run_main() -> None:
    """Sync wrapper for console script entry point."""
    asyncio.run(main())


async def main() -> None:
    """Main entry point for running the server.

    Run with stdio transport (default for Claude Desktop):
        python -m remote_terminal_mcp.server
        uv run remote-terminal-mcp
    """
    # For stdio transport (default)
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="remote-terminal",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
