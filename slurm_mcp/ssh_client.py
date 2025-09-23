"""SSH client for connecting to SLURM clusters."""

import logging
from typing import Optional, Tuple, Dict, Any
import paramiko


logger = logging.getLogger(__name__)


class SSHClient:
    """SSH client for executing commands on remote SLURM clusters."""
    
    def __init__(self, hostname: str, username: str, password: Optional[str] = None,
                 key_filename: Optional[str] = None, port: int = 22):
        """Initialize SSH client.
        
        Args:
            hostname: Remote host to connect to
            username: Username for SSH connection
            password: Password for SSH connection (optional if using key)
            key_filename: Path to private key file (optional if using password)
            port: SSH port (default: 22)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.client: Optional[paramiko.SSHClient] = None
        
    def connect(self) -> None:
        """Establish SSH connection."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs: Dict[str, Any] = {
                'hostname': self.hostname,
                'username': self.username,
                'port': self.port,
                'timeout': 30,
            }
            
            if self.key_filename:
                connect_kwargs['key_filename'] = self.key_filename
            elif self.password:
                connect_kwargs['password'] = self.password
            else:
                raise ValueError("Either password or key_filename must be provided")
                
            self.client.connect(**connect_kwargs)
            logger.info(f"Successfully connected to {self.hostname}")
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.hostname}: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close SSH connection."""
        if self.client:
            self.client.close()
            self.client = None
            logger.info(f"Disconnected from {self.hostname}")
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute a command on the remote host.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        if not self.client:
            raise RuntimeError("SSH client not connected. Call connect() first.")
        
        try:
            logger.debug(f"Executing command: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            stdout_str = stdout.read().decode('utf-8').strip()
            stderr_str = stderr.read().decode('utf-8').strip()
            exit_code = stdout.channel.recv_exit_status()
            
            logger.debug(f"Command exit code: {exit_code}")
            if stderr_str:
                logger.warning(f"Command stderr: {stderr_str}")
                
            return stdout_str, stderr_str, exit_code
            
        except Exception as e:
            logger.error(f"Failed to execute command '{command}': {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()