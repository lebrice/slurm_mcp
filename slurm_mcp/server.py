"""SLURM MCP Server - Main server implementation."""

import os
import logging
from typing import Optional, Dict, Any, List
import json

from fastmcp import FastMCP
from .ssh_client import SSHClient
from .slurm_commands import SlurmClient


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create MCP server instance
mcp = FastMCP("SLURM Cluster Interface")

# Global variables for SSH and SLURM clients
ssh_client: Optional[SSHClient] = None
slurm_client: Optional[SlurmClient] = None


def get_connection_config() -> Dict[str, Any]:
    """Get SSH connection configuration from environment variables."""
    return {
        "hostname": os.getenv("SLURM_HOST", "localhost"),
        "username": os.getenv("SLURM_USER", os.getenv("USER", "user")),
        "password": os.getenv("SLURM_PASSWORD"),
        "key_filename": os.getenv("SLURM_KEY_FILE", os.path.expanduser("~/.ssh/id_rsa")),
        "port": int(os.getenv("SLURM_PORT", "22"))
    }


def ensure_connection() -> SlurmClient:
    """Ensure SSH connection is established and return SLURM client."""
    global ssh_client, slurm_client
    
    if not ssh_client or not slurm_client:
        config = get_connection_config()
        ssh_client = SSHClient(**config)
        ssh_client.connect()
        slurm_client = SlurmClient(ssh_client)
        logger.info(f"Connected to SLURM cluster at {config['hostname']}")
    
    return slurm_client


@mcp.tool()
def squeue(
    user: Optional[str] = None,
    job_id: Optional[str] = None,
    partition: Optional[str] = None,
    format_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query the SLURM job queue to see running and pending jobs.
    
    Args:
        user: Filter jobs by username
        job_id: Show specific job by ID
        partition: Filter jobs by partition/queue name
        format_str: Custom format string for output (advanced users)
    
    Returns:
        Dictionary containing job queue information
    """
    try:
        client = ensure_connection()
        result = client.squeue(user=user, job_id=job_id, partition=partition, format_str=format_str)
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["stdout"],
                "command": result["command"]
            }
        else:
            return {
                "status": "error",
                "error": result["stderr"],
                "command": result["command"]
            }
    except Exception as e:
        logger.error(f"Error in squeue: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def sinfo(
    partition: Optional[str] = None,
    format_str: Optional[str] = None,
    nodes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query SLURM cluster information including partitions and node status.
    
    Args:
        partition: Show information for specific partition
        format_str: Custom format string for output (advanced users)
        nodes: Show information for specific nodes (comma-separated)
    
    Returns:
        Dictionary containing cluster information
    """
    try:
        client = ensure_connection()
        result = client.sinfo(partition=partition, format_str=format_str, nodes=nodes)
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["stdout"],
                "command": result["command"]
            }
        else:
            return {
                "status": "error",
                "error": result["stderr"],
                "command": result["command"]
            }
    except Exception as e:
        logger.error(f"Error in sinfo: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def sacct(
    job_id: Optional[str] = None,
    user: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    format_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query SLURM job accounting information for completed jobs.
    
    Args:
        job_id: Show accounting info for specific job ID
        user: Filter jobs by username
        start_time: Start time for query (format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        end_time: End time for query (format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        format_str: Custom format string for output (advanced users)
    
    Returns:
        Dictionary containing job accounting information
    """
    try:
        client = ensure_connection()
        result = client.sacct(
            job_id=job_id, 
            user=user, 
            start_time=start_time, 
            end_time=end_time, 
            format_str=format_str
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["stdout"],
                "command": result["command"]
            }
        else:
            return {
                "status": "error",
                "error": result["stderr"],
                "command": result["command"]
            }
    except Exception as e:
        logger.error(f"Error in sacct: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def scontrol_show_job(job_id: str) -> Dict[str, Any]:
    """
    Show detailed information about a specific SLURM job.
    
    Args:
        job_id: Job ID to show details for
    
    Returns:
        Dictionary containing detailed job information
    """
    try:
        client = ensure_connection()
        result = client.scontrol_show_job(job_id)
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["stdout"],
                "command": result["command"]
            }
        else:
            return {
                "status": "error",
                "error": result["stderr"],
                "command": result["command"]
            }
    except Exception as e:
        logger.error(f"Error in scontrol_show_job: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def scontrol_show_node(node_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Show detailed information about SLURM nodes.
    
    Args:
        node_name: Specific node name to show (if None, shows all nodes)
    
    Returns:
        Dictionary containing detailed node information
    """
    try:
        client = ensure_connection()
        result = client.scontrol_show_node(node_name)
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["stdout"],
                "command": result["command"]
            }
        else:
            return {
                "status": "error",
                "error": result["stderr"],
                "command": result["command"]
            }
    except Exception as e:
        logger.error(f"Error in scontrol_show_node: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def scancel(job_id: str) -> Dict[str, Any]:
    """
    Cancel a SLURM job.
    
    Args:
        job_id: Job ID to cancel
    
    Returns:
        Dictionary indicating success or failure of job cancellation
    """
    try:
        client = ensure_connection()
        result = client.scancel(job_id)
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Job {job_id} cancelled successfully",
                "command": result["command"]
            }
        else:
            return {
                "status": "error",
                "error": result["stderr"],
                "command": result["command"]
            }
    except Exception as e:
        logger.error(f"Error in scancel: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def get_connection_status() -> Dict[str, Any]:
    """
    Check the status of the SSH connection to the SLURM cluster.
    
    Returns:
        Dictionary containing connection status information
    """
    try:
        config = get_connection_config()
        
        # Check if we have a connection
        if ssh_client and ssh_client.client:
            # Test the connection with a simple command
            stdout, stderr, exit_code = ssh_client.execute_command("echo 'connection test'")
            if exit_code == 0:
                return {
                    "status": "connected",
                    "hostname": config["hostname"],
                    "username": config["username"],
                    "port": config["port"]
                }
        
        return {
            "status": "disconnected",
            "hostname": config["hostname"],
            "username": config["username"],
            "port": config["port"]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def disconnect() -> Dict[str, str]:
    """
    Disconnect from the SLURM cluster.
    
    Returns:
        Dictionary indicating disconnection status
    """
    global ssh_client, slurm_client
    
    try:
        if ssh_client:
            ssh_client.disconnect()
            ssh_client = None
            slurm_client = None
        
        return {
            "status": "success",
            "message": "Disconnected from SLURM cluster"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def main():
    """Main entry point for the MCP server."""
    try:
        # Add cleanup on exit
        import atexit
        atexit.register(lambda: disconnect() if ssh_client else None)
        
        # Start the MCP server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        disconnect()
    except Exception as e:
        logger.error(f"Server error: {e}")
        disconnect()
        raise


if __name__ == "__main__":
    main()