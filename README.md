# Remote Terminal MCP Server

A Model Context Protocol (MCP) server that provides secure command execution capabilities with both stdio and HTTP/SSE transport options for integration with AI assistants like Claude.

## Features

- **Full shell command execution** - Run any shell command with proper output capture
- **Dual transport support** - Stdio for local, HTTP/SSE for remote/cross-machine access
- **Safety validation** - Input validation and timeout protection
- **Structured output** - Pydantic models for type-safe command results
- **System resources** - Access system information and environment variables
- **Type hints** - Full type annotations for IDE support
- **Async patterns** - Built on asyncio for efficient concurrent operations

## Installation

### Using uv (recommended)

```bash
# Clone or navigate to the project directory
cd remote-terminal-mcp

# Install dependencies (automatically creates virtual environment)
uv sync
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Usage

### Transport Options

This MCP server supports two transport modes:

1. **stdio transport** (`remote-terminal-mcp`) - For local integration with Claude Desktop
2. **HTTP/SSE transport** (`remote-terminal-mcp-http`) - For remote/cross-machine access

### Running the Server

#### Stdio Transport (Local)

```bash
# Using uv
uv run remote-terminal-mcp

# Or using python directly
python -m remote_terminal_mcp.server
```

#### HTTP/SSE Transport (Remote)

```bash
# Using uv (default: 0.0.0.0:8080)
uv run remote-terminal-mcp-http

# Custom host/port
uv run remote-terminal-mcp-http --host 127.0.0.1 --port 9000

# Or via environment variables
MCP_HOST=0.0.0.0 MCP_PORT=8080 uv run remote-terminal-mcp-http
```

**Important:** The HTTP/SSE server binds to `0.0.0.0` by default, making it accessible from other machines. Ensure you have proper firewall rules and consider implementing authentication for production use.

### Connecting Clients

#### Using Claude Desktop (stdio)

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "remote-terminal": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/remote-terminal-mcp",
        "run",
        "remote-terminal-mcp"
      ]
    }
  }
}
```

#### Using HTTP/SSE (Remote/Cross-Machine)

For remote access, start the HTTP server:

```bash
# On the server machine
uv run remote-terminal-mcp-http --host 0.0.0.0 --port 8080
```

Then connect from your MCP client using:
- SSE endpoint: `http://server-ip:8080/sse`
- Messages endpoint: `http://server-ip:8080/messages/`

#### Using MCP Inspector

For testing and development:

```bash
# Install the MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Test stdio transport
npx @modelcontextprotocol/inspector uv run remote-terminal-mcp

# Test HTTP/SSE transport (requires separate terminal)
# Terminal 1: Start the server
uv run remote-terminal-mcp-http

# Terminal 2: Connect inspector to http://localhost:8080/sse
```

## Available Tools

### execute_command

Execute shell commands on the system.

**Parameters:**
- `command` (string, required): Shell command to execute
- `working_dir` (string, optional): Working directory for command execution
- `timeout` (integer, optional): Command timeout in seconds (default: 30, max: 300)
- `env` (object, optional): Environment variables for the command

**Returns:**
- `return_code` (integer): Process exit code
- `stdout` (string): Standard output
- `stderr` (string): Standard error output
- `success` (boolean): Whether command succeeded (exit code 0)

**Examples:**

```json
// List files
{"command": "ls -la"}

// With working directory
{"command": "pwd", "working_dir": "/tmp"}

// With environment variable
{"command": "echo $MY_VAR", "env": {"MY_VAR": "hello"}}

// With timeout
{"command": "sleep 10", "timeout": 15}
```

## Available Resources

### system://info

Get basic system information including platform, Python version, hostname, etc.

```json
{
  "platform": "Linux-6.5.0-x86_64",
  "system": "Linux",
  "release": "6.5.0",
  "python_version": "3.12.0",
  "current_directory": "/home/user",
  "hostname": "myserver"
}
```

### system://environment

Get environment variables (sensitive values are redacted).

```json
{
  "PATH": "/usr/bin:/bin",
  "HOME": "/home/user",
  "SECRET_TOKEN": "***REDACTED***"
}
```

## Security Considerations

**WARNING: This server provides full command execution capabilities. Use with extreme caution.**

### HTTP/SSE Transport Security

The HTTP/SSE transport allows **remote/cross-machine access** to command execution:

1. **No authentication by default** - Anyone who can reach the port can execute commands
2. **Use behind a firewall** - Restrict access to trusted networks only
3. **Consider adding authentication** - Implement API keys, OAuth, or other auth mechanisms
4. **Use HTTPS** - For production deployment, use TLS/SSL encryption
5. **Network isolation** - Run in a isolated network segment when possible

### Command Validation

The server includes basic validation for dangerous patterns, but:

- Always sanitize user input
- Consider implementing allowlists for permitted commands
- Review and audit command logs
- Set appropriate timeout limits

### Environment Exposure

Sensitive environment variables are redacted, but:

- Review the `system://environment` resource implementation
- Consider restricting access to system resources
- Be aware of what environment variables are exposed

### Production Deployment

For production use:

- Run with minimal required permissions
- Set up proper logging and monitoring
- Implement authentication/authorization
- Use rate limiting to prevent abuse
- Keep dependencies updated

## Development

### Project Structure

```
remote-terminal-mcp/
├── src/
│   └── remote_terminal_mcp/
│       ├── __init__.py
│       └── server.py
├── pyproject.toml
├── README.md
└── .gitignore
```

### Adding New Tools

Edit `src/remote_terminal_mcp/server.py`:

```python
@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"
```

### Running Tests

```bash
# Run with uv
uv run pytest

# Or with MCP Inspector for interactive testing
npx @modelcontextprotocol/inspector uv run remote-terminal-mcp
```

## Requirements

- Python 3.11+
- uv (recommended) or pip
- MCP Python SDK 1.26.0+

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.

## Support

For issues, questions, or contributions, please visit the project repository.

## References

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Anthropic MCP Documentation](https://docs.anthropic.com/)
