# slurm_mcp

[![CI](https://github.com/lebrice/slurm_mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/lebrice/slurm_mcp/actions/workflows/ci.yml)

Simple MCP server to interact with SLURM clusters in natural language.

## Features

- Allows LLM agents to retrieve information on running jobs from `squeue`, prior jobs from `sacct`, and to get compute usage information based on Prometheus (mila cluster only for now).

## Demo

<img width="974" height="903" alt="Screenshot from 2025-10-03 15-04-03" src="https://github.com/user-attachments/assets/4f277e02-ab8e-468a-9b4e-a9c18f3256a8" />

## Setup

You need to have SSH access to a SLURM compute cluster.

1. Install [UV](https://docs.astral.sh/uv) following the instructions [here](https://docs.astral.sh/uv/getting-started/installation).

2. Create a `.vscode/mcp.json` file with the following content:

```json
{
    "servers": {
        "slurm_mcp": {
            "type": "stdio",
            "command": "uvx",
            "args": [
                "--from",
                "git+https://www.github.com/lebrice/slurm_mcp",
                "slurm_mcp"
            ]
        }
    }
}
```

3. To get GPU metrics, you need to set the `PROMETHEUS_URL_<CLUSTER>` environment variable to the Prometheus URL of your cluster. If the SLURM cluster requires authentication to connect to prometheus, you also need to set the `PROMETHEUS_HEADERS_FILE_<CLUSTER>` environment variable to point to a JSON file containing the headers to use for authentication (e.g., `{"Authorization": "Bearer <TOKEN>"}`).

   - you can set these environment variables in your shell configuration file (e.g., `.bashrc`, `.bash_aliases`, `.zshrc`, etc.):

   ```bash
   export PROMETHEUS_URL_MILA="THE_MILA_PROMETHEUS_URL"
   export PROMETHEUS_HEADERS_FILE="my/secrets/prometheus_headers_mila.json"
    ```


## Limitations

- This can only fetch your own SLURM job information, not of other users.
- This can't be used to launch jobs. It is not a good idea to let an LLM submit compute jobs for you.
- The GPU utilization metrics are only available for the Mila cluster. For other clusters, you will need to provide the prometheus URL to use in order to fetch job compute stats.
   - Some jobs are missing GPU compute stats because of a bug in the DCGMI / slurm job exporter / nvidia driver / something, that causes the gpu util to be a very very very large number. This tool filters those and displays them as having no usable compute metrics.



