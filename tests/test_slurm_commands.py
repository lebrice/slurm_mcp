"""Tests for SLURM commands module."""

from unittest.mock import Mock

from slurm_mcp.slurm_commands import SlurmClient


class TestSlurmClient:
    """Test SLURM client functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_ssh_client = Mock()
        self.slurm_client = SlurmClient(self.mock_ssh_client)

    def test_init(self):
        """Test SLURM client initialization."""
        assert self.slurm_client.ssh_client == self.mock_ssh_client

    def test_squeue_basic(self):
        """Test basic squeue command."""
        self.mock_ssh_client.execute_command.return_value = (
            "JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST",
            "",
            0,
        )

        result = self.slurm_client.squeue()

        expected_cmd = 'squeue -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"'
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)

        assert result["success"] is True
        assert result["command"] == expected_cmd
        assert "JOBID" in result["stdout"]
        assert result["stderr"] == ""
        assert result["exit_code"] == 0

    def test_squeue_with_parameters(self):
        """Test squeue with various parameters."""
        self.mock_ssh_client.execute_command.return_value = ("output", "", 0)

        result = self.slurm_client.squeue(
            user="testuser", job_id="12345", partition="gpu", format_str="%.10i %.8u"
        )

        expected_cmd = 'squeue -o "%.10i %.8u" -u testuser -j 12345 -p gpu'
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)
        assert result["success"] is True

    def test_sinfo_basic(self):
        """Test basic sinfo command."""
        self.mock_ssh_client.execute_command.return_value = (
            "PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST",
            "",
            0,
        )

        result = self.slurm_client.sinfo()

        expected_cmd = 'sinfo -o "%.20P %.5a %.10l %.6D %.6t %.14N"'
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)

        assert result["success"] is True
        assert "PARTITION" in result["stdout"]

    def test_sinfo_with_parameters(self):
        """Test sinfo with parameters."""
        self.mock_ssh_client.execute_command.return_value = ("output", "", 0)

        result = self.slurm_client.sinfo(
            partition="gpu", nodes="node01,node02", format_str="%.10P %.5a"
        )

        expected_cmd = 'sinfo -o "%.10P %.5a" -p gpu -n node01,node02'
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)
        assert result["success"] is True

    def test_sacct_basic(self):
        """Test basic sacct command."""
        self.mock_ssh_client.execute_command.return_value = (
            "JobID    JobName  Partition    Account  AllocCPUS      State ExitCode",
            "",
            0,
        )

        result = self.slurm_client.sacct()

        expected_cmd = (
            "sacct --format JobID,JobName,Partition,Account,AllocCPUS,State,ExitCode"
        )
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)

        assert result["success"] is True
        assert "JobID" in result["stdout"]

    def test_sacct_with_parameters(self):
        """Test sacct with parameters."""
        self.mock_ssh_client.execute_command.return_value = ("output", "", 0)

        result = self.slurm_client.sacct(
            job_id="12345",
            user="testuser",
            start_time="2023-01-01",
            end_time="2023-12-31",
            format_str="JobID,JobName,State",
        )

        expected_cmd = (
            "sacct --format JobID,JobName,State -j 12345 -u testuser "
            "-S 2023-01-01 -E 2023-12-31"
        )
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)
        assert result["success"] is True

    def test_scontrol_show_job(self):
        """Test scontrol show job command."""
        self.mock_ssh_client.execute_command.return_value = (
            "JobId=12345 JobName=test_job\nUserId=testuser(1000) GroupId=users(100)",
            "",
            0,
        )

        result = self.slurm_client.scontrol_show_job("12345")

        expected_cmd = "scontrol show job 12345"
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)

        assert result["success"] is True
        assert "JobId=12345" in result["stdout"]

    def test_scontrol_show_node_specific(self):
        """Test scontrol show node for specific node."""
        self.mock_ssh_client.execute_command.return_value = (
            "NodeName=node01 Arch=x86_64 CoresPerSocket=16",
            "",
            0,
        )

        result = self.slurm_client.scontrol_show_node("node01")

        expected_cmd = "scontrol show node node01"
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)

        assert result["success"] is True
        assert "NodeName=node01" in result["stdout"]

    def test_scontrol_show_node_all(self):
        """Test scontrol show nodes for all nodes."""
        self.mock_ssh_client.execute_command.return_value = (
            "NodeName=node01 NodeName=node02",
            "",
            0,
        )

        result = self.slurm_client.scontrol_show_node()

        expected_cmd = "scontrol show nodes"
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)

        assert result["success"] is True

    def test_scancel(self):
        """Test scancel command."""
        self.mock_ssh_client.execute_command.return_value = ("", "", 0)

        result = self.slurm_client.scancel("12345")

        expected_cmd = "scancel 12345"
        self.mock_ssh_client.execute_command.assert_called_once_with(expected_cmd)

        assert result["success"] is True
        assert result["command"] == expected_cmd

    def test_command_failure(self):
        """Test handling of command failures."""
        self.mock_ssh_client.execute_command.return_value = (
            "",
            "squeue: error: Authentication failure",
            1,
        )

        result = self.slurm_client.squeue()

        assert result["success"] is False
        assert result["exit_code"] == 1
        assert "Authentication failure" in result["stderr"]
