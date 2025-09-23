# SLURM MCP Server

A simple MCP (Model Context Protocol) server to interact with SLURM clusters over SSH using the [fastmcp Python package](https://gofastmcp.com/).

## Features

- **SSH Connection**: Secure connection to SLURM clusters using SSH with password or key-based authentication
- **SLURM Commands**: Execute common SLURM commands remotely:
  - `squeue` - Query job queue status
  - `sinfo` - Get cluster/partition information
  - `sacct` - View job accounting data
  - `scontrol show job` - Get detailed job information
  - `scontrol show node` - Get detailed node information
  - `scancel` - Cancel jobs
- **Connection Management**: Built-in connection status checking and cleanup
- **Error Handling**: Comprehensive error handling and logging

## Installation

### From Source

```bash
git clone https://github.com/lebrice/slurm_mcp.git
cd slurm_mcp
pip install -e .
```

### Using pip (when available)

```bash
pip install slurm_mcp
```

## Configuration

Configure your SLURM cluster connection using environment variables. Copy the example configuration:

```bash
cp .env.example .env
```

Edit `.env` with your cluster details:

```bash
# SSH connection details
SLURM_HOST=your-cluster-hostname.example.com
SLURM_USER=your-username
SLURM_PORT=22

# Authentication (choose one method)
# Option 1: Password authentication
SLURM_PASSWORD=your-password

# Option 2: SSH key authentication (preferred)
SLURM_KEY_FILE=/path/to/your/private/key
```

## Usage

### Starting the MCP Server

```bash
slurm-mcp
```

The server will start and listen for MCP client connections over STDIO.

### Available Tools

The server provides the following tools that can be called by MCP clients:

#### `squeue`
Query the SLURM job queue to see running and pending jobs.

**Parameters:**
- `user` (optional): Filter jobs by username
- `job_id` (optional): Show specific job by ID
- `partition` (optional): Filter jobs by partition/queue name
- `format_str` (optional): Custom format string for output

#### `sinfo`
Query SLURM cluster information including partitions and node status.

**Parameters:**
- `partition` (optional): Show information for specific partition
- `nodes` (optional): Show information for specific nodes (comma-separated)
- `format_str` (optional): Custom format string for output

#### `sacct`
Query SLURM job accounting information for completed jobs.

**Parameters:**
- `job_id` (optional): Show accounting info for specific job ID
- `user` (optional): Filter jobs by username
- `start_time` (optional): Start time for query (format: YYYY-MM-DD)
- `end_time` (optional): End time for query (format: YYYY-MM-DD)
- `format_str` (optional): Custom format string for output

#### `scontrol_show_job`
Show detailed information about a specific SLURM job.

**Parameters:**
- `job_id` (required): Job ID to show details for

#### `scontrol_show_node`
Show detailed information about SLURM nodes.

**Parameters:**
- `node_name` (optional): Specific node name to show (if None, shows all nodes)

#### `scancel`
Cancel a SLURM job.

**Parameters:**
- `job_id` (required): Job ID to cancel

#### `get_connection_status`
Check the status of the SSH connection to the SLURM cluster.

#### `disconnect`
Disconnect from the SLURM cluster.

## Example Usage with MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="slurm-mcp",
        args=[],
        env={}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the client
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools.tools])
            
            # Check connection status
            result = await session.call_tool("get_connection_status", {})
            print("Connection status:", result.content)
            
            # Query job queue
            result = await session.call_tool("squeue", {"user": "myusername"})
            print("Job queue:", result.content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Development

### Running Tests

```bash
pip install pytest
pytest tests/
```

### Code Formatting

```bash
pip install black ruff
black slurm_mcp/
ruff check slurm_mcp/
```

### Type Checking

```bash
pip install mypy
mypy slurm_mcp/
```

## Security Considerations

- Use SSH key authentication instead of passwords when possible
- Ensure your SSH private keys have appropriate permissions (600)
- Consider using SSH agent forwarding for enhanced security
- The server automatically adds unknown host keys (uses `AutoAddPolicy`)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [FastMCP](https://gofastmcp.com/) - The Python package used to build this MCP server
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification
