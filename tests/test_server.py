"""Tests for the SLURM MCP server."""

import pytest
from unittest.mock import Mock, patch
from slurm_mcp.server import get_connection_config


class TestServerFunctions:
    """Test server functions."""
    
    def test_get_connection_config_defaults(self):
        """Test getting connection config with defaults."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('os.getenv') as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    'SLURM_HOST': 'localhost',
                    'SLURM_USER': 'testuser',  
                    'USER': 'testuser',
                    'SLURM_PORT': '22'
                }.get(key, default)
                
                config = get_connection_config()
                
                assert config['hostname'] == 'localhost'
                assert config['username'] == 'testuser'
                assert config['port'] == 22
    
    def test_get_connection_config_with_env_vars(self):
        """Test getting connection config with custom environment variables."""
        env_vars = {
            'SLURM_HOST': 'cluster.example.com',
            'SLURM_USER': 'myuser',
            'SLURM_PASSWORD': 'mypass',
            'SLURM_PORT': '2222'
        }
        
        with patch.dict('os.environ', env_vars):
            config = get_connection_config()
            
            assert config['hostname'] == 'cluster.example.com'
            assert config['username'] == 'myuser'
            assert config['password'] == 'mypass'
            assert config['port'] == 2222
    
    def test_server_imports(self):
        """Test that all server components can be imported."""
        from slurm_mcp.server import mcp
        from slurm_mcp.ssh_client import SSHClient
        from slurm_mcp.slurm_commands import SlurmClient
        
        # Test that we can import the main components
        assert mcp is not None
        assert SSHClient is not None
        assert SlurmClient is not None