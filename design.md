Create an MCP server with fastmcp that retrieves information about SLURM jobs from a configurable list of hostnames (remote SLURM clusters) via SSH.

- use `ssh <cluster> sacct --json (...)` to retrieve jobs info, and parse the job info into nicely structured pydantic SlurmJob objects.
- The MCP should have an endpoint to view the current jobs on a given cluster.
