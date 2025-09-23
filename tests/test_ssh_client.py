"""Tests for SSH client functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from slurm_mcp.ssh_client import SSHClient


class TestSSHClient:
    """Test cases for SSHClient class."""
    
    def test_init(self):
        """Test SSH client initialization."""
        client = SSHClient(
            hostname="test.example.com",
            username="testuser",
            password="testpass",
            port=22
        )
        
        assert client.hostname == "test.example.com"
        assert client.username == "testuser"
        assert client.password == "testpass"
        assert client.port == 22
        assert client.client is None
    
    def test_init_with_key_file(self):
        """Test SSH client initialization with key file."""
        client = SSHClient(
            hostname="test.example.com",
            username="testuser",
            key_filename="/path/to/key",
            port=2222
        )
        
        assert client.hostname == "test.example.com"
        assert client.username == "testuser"
        assert client.key_filename == "/path/to/key"
        assert client.port == 2222
    
    @patch('slurm_mcp.ssh_client.paramiko.SSHClient')
    def test_connect_with_password(self, mock_ssh_class):
        """Test SSH connection with password."""
        mock_ssh = Mock()
        mock_ssh_class.return_value = mock_ssh
        
        client = SSHClient(
            hostname="test.example.com",
            username="testuser",
            password="testpass"
        )
        
        client.connect()
        
        mock_ssh_class.assert_called_once()
        mock_ssh.set_missing_host_key_policy.assert_called_once()
        mock_ssh.connect.assert_called_once_with(
            hostname="test.example.com",
            username="testuser",
            port=22,
            timeout=30,
            password="testpass"
        )
    
    @patch('slurm_mcp.ssh_client.paramiko.SSHClient')
    def test_connect_with_key_file(self, mock_ssh_class):
        """Test SSH connection with key file."""
        mock_ssh = Mock()
        mock_ssh_class.return_value = mock_ssh
        
        client = SSHClient(
            hostname="test.example.com",
            username="testuser",
            key_filename="/path/to/key"
        )
        
        client.connect()
        
        mock_ssh.connect.assert_called_once_with(
            hostname="test.example.com",
            username="testuser",
            port=22,
            timeout=30,
            key_filename="/path/to/key"
        )
    
    def test_connect_without_auth(self):
        """Test SSH connection without authentication raises error."""
        client = SSHClient(
            hostname="test.example.com",
            username="testuser"
        )
        
        with pytest.raises(ValueError, match="Either password or key_filename must be provided"):
            client.connect()
    
    @patch('slurm_mcp.ssh_client.paramiko.SSHClient')
    def test_execute_command(self, mock_ssh_class):
        """Test command execution."""
        mock_ssh = Mock()
        mock_ssh_class.return_value = mock_ssh
        
        # Mock the exec_command return values
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        
        mock_stdout.read.return_value = b"test output\n"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        
        mock_ssh.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        
        client = SSHClient(
            hostname="test.example.com",
            username="testuser",
            password="testpass"
        )
        client.connect()
        
        stdout, stderr, exit_code = client.execute_command("echo 'test'")
        
        assert stdout == "test output"
        assert stderr == ""
        assert exit_code == 0
        mock_ssh.exec_command.assert_called_with("echo 'test'", timeout=30)
    
    def test_execute_command_without_connection(self):
        """Test command execution without connection raises error."""
        client = SSHClient(
            hostname="test.example.com",
            username="testuser",
            password="testpass"
        )
        
        with pytest.raises(RuntimeError, match="SSH client not connected"):
            client.execute_command("echo 'test'")
    
    @patch('slurm_mcp.ssh_client.paramiko.SSHClient')
    def test_disconnect(self, mock_ssh_class):
        """Test SSH disconnection."""
        mock_ssh = Mock()
        mock_ssh_class.return_value = mock_ssh
        
        client = SSHClient(
            hostname="test.example.com",
            username="testuser",
            password="testpass"
        )
        client.connect()
        client.disconnect()
        
        mock_ssh.close.assert_called_once()
        assert client.client is None
    
    @patch('slurm_mcp.ssh_client.paramiko.SSHClient')
    def test_context_manager(self, mock_ssh_class):
        """Test context manager functionality."""
        mock_ssh = Mock()
        mock_ssh_class.return_value = mock_ssh
        
        client = SSHClient(
            hostname="test.example.com",
            username="testuser",
            password="testpass"
        )
        
        with client as c:
            assert c is client
            mock_ssh.connect.assert_called_once()
        
        mock_ssh.close.assert_called_once()