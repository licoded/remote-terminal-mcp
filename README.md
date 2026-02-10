# Remote Terminal MCP Server

A Model Context Protocol (MCP) server that provides secure command execution capabilities with stdio transport for integration with AI assistants like Claude.

## Features

- **Full shell command execution** - Run any shell command with proper output capture
- **Stdio transport** - Direct integration with Claude Desktop and other MCP clients
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

### Running the Server

The server uses stdio transport, which is the standard for MCP client integration:

```bash
# Using uv
uv run remote-terminal-mcp

# Or using python directly
python -m remote_terminal_mcp.server
```

### Connecting Clients

#### Using Claude Desktop

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

Replace `/path/to/remote-terminal-mcp` with the actual path to your project directory.

#### Using MCP Inspector

For testing and development:

```bash
# Install the MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run the inspector with the server
npx @modelcontextprotocol/inspector uv run remote-terminal-mcp
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

This server provides full command execution capabilities. Important security notes:

1. **Command validation** - The server includes basic validation for dangerous patterns, but:
   - Always sanitize user input
   - Consider implementing allowlists for permitted commands
   - Review and audit command logs

2. **Environment exposure** - Sensitive environment variables are redacted, but:
   - Review the `system://environment` resource implementation
   - Consider restricting access to system resources

3. **Production deployment** - For production use:
   - Run with minimal required permissions
   - Set up proper logging and monitoring
   - Consider implementing additional authentication/authorization

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
