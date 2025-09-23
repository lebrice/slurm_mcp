"""SLURM command wrappers for common operations."""

import logging
from typing import Dict, List, Optional, Any
from .ssh_client import SSHClient


logger = logging.getLogger(__name__)


class SlurmClient:
    """Client for executing SLURM commands via SSH."""
    
    def __init__(self, ssh_client: SSHClient):
        """Initialize SLURM client with SSH connection.
        
        Args:
            ssh_client: Connected SSH client instance
        """
        self.ssh_client = ssh_client
    
    def squeue(self, user: Optional[str] = None, job_id: Optional[str] = None,
               partition: Optional[str] = None, format_str: Optional[str] = None) -> Dict[str, Any]:
        """Query job queue information.
        
        Args:
            user: Filter by username
            job_id: Filter by specific job ID
            partition: Filter by partition name
            format_str: Custom format string for squeue output
            
        Returns:
            Dictionary with command output and metadata
        """
        cmd = ["squeue"]
        
        if format_str:
            cmd.extend(["-o", f'"{format_str}"'])
        else:
            # Default format with useful fields
            cmd.extend(["-o", '"%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"'])
        
        if user:
            cmd.extend(["-u", user])
        if job_id:
            cmd.extend(["-j", job_id])
        if partition:
            cmd.extend(["-p", partition])
        
        command = " ".join(cmd)
        stdout, stderr, exit_code = self.ssh_client.execute_command(command)
        
        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "success": exit_code == 0
        }
    
    def sinfo(self, partition: Optional[str] = None, format_str: Optional[str] = None,
              nodes: Optional[str] = None) -> Dict[str, Any]:
        """Query cluster/partition information.
        
        Args:
            partition: Filter by partition name
            format_str: Custom format string for sinfo output
            nodes: Filter by node names
            
        Returns:
            Dictionary with command output and metadata
        """
        cmd = ["sinfo"]
        
        if format_str:
            cmd.extend(["-o", f'"{format_str}"'])
        else:
            # Default format with useful fields
            cmd.extend(["-o", '"%.20P %.5a %.10l %.6D %.6t %.14N"'])
        
        if partition:
            cmd.extend(["-p", partition])
        if nodes:
            cmd.extend(["-n", nodes])
        
        command = " ".join(cmd)
        stdout, stderr, exit_code = self.ssh_client.execute_command(command)
        
        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "success": exit_code == 0
        }
    
    def sacct(self, job_id: Optional[str] = None, user: Optional[str] = None,
              start_time: Optional[str] = None, end_time: Optional[str] = None,
              format_str: Optional[str] = None) -> Dict[str, Any]:
        """Query accounting information for jobs.
        
        Args:
            job_id: Filter by specific job ID
            user: Filter by username
            start_time: Start time for query (format: YYYY-MM-DD)
            end_time: End time for query (format: YYYY-MM-DD)
            format_str: Custom format string for sacct output
            
        Returns:
            Dictionary with command output and metadata
        """
        cmd = ["sacct"]
        
        if format_str:
            cmd.extend(["--format", format_str])
        else:
            # Default format with useful fields
            cmd.extend(["--format", "JobID,JobName,Partition,Account,AllocCPUS,State,ExitCode"])
        
        if job_id:
            cmd.extend(["-j", job_id])
        if user:
            cmd.extend(["-u", user])
        if start_time:
            cmd.extend(["-S", start_time])
        if end_time:
            cmd.extend(["-E", end_time])
        
        command = " ".join(cmd)
        stdout, stderr, exit_code = self.ssh_client.execute_command(command)
        
        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "success": exit_code == 0
        }
    
    def scontrol_show_job(self, job_id: str) -> Dict[str, Any]:
        """Show detailed information about a specific job.
        
        Args:
            job_id: Job ID to query
            
        Returns:
            Dictionary with command output and metadata
        """
        command = f"scontrol show job {job_id}"
        stdout, stderr, exit_code = self.ssh_client.execute_command(command)
        
        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "success": exit_code == 0
        }
    
    def scontrol_show_node(self, node_name: Optional[str] = None) -> Dict[str, Any]:
        """Show detailed information about nodes.
        
        Args:
            node_name: Specific node to query (if None, shows all nodes)
            
        Returns:
            Dictionary with command output and metadata
        """
        if node_name:
            command = f"scontrol show node {node_name}"
        else:
            command = "scontrol show nodes"
        
        stdout, stderr, exit_code = self.ssh_client.execute_command(command)
        
        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "success": exit_code == 0
        }
    
    def scancel(self, job_id: str) -> Dict[str, Any]:
        """Cancel a job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            Dictionary with command output and metadata
        """
        command = f"scancel {job_id}"
        stdout, stderr, exit_code = self.ssh_client.execute_command(command)
        
        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "success": exit_code == 0
        }