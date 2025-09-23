#!/usr/bin/env python3
"""Demo script to test SLURM MCP server functionality."""

from slurm_mcp.server import get_connection_config, get_connection_status, sinfo, squeue


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*50}")
    print(f" {title}")
    print("=" * 50)


def main():
    """Demo the SLURM MCP server functionality."""
    print("SLURM MCP Server Demo")
    print("=====================")

    # Show configuration
    print_section("Configuration")
    config = get_connection_config()
    print(f"Hostname: {config['hostname']}")
    print(f"Username: {config['username']}")
    print(f"Port: {config['port']}")
    print(f"Key file: {config.get('key_filename', 'Not set')}")
    print(f"Password: {'Set' if config.get('password') else 'Not set'}")

    # Check if we have proper configuration
    if config["hostname"] == "localhost":
        print("\n⚠️  WARNING: Using default localhost configuration!")
        print("   Set SLURM_HOST environment variable to connect to a real cluster.")
        print("   This demo will only work if you have SLURM running locally.")

        response = input("\nContinue with localhost demo? (y/N): ")
        if response.lower() != "y":
            print("Exiting. Configure environment variables and try again.")
            return

    # Test connection status
    print_section("Connection Status")
    try:
        status = get_connection_status()
        print(f"Status: {status}")
    except Exception as e:
        print(f"Error checking connection: {e}")
        print("Make sure your SSH credentials are configured correctly.")
        return

    # Test squeue
    print_section("Testing squeue (Job Queue)")
    try:
        result = squeue()
        if result["status"] == "success":
            print("✅ squeue successful:")
            print(result["data"])
        else:
            print("❌ squeue failed:")
            print(result.get("error", "Unknown error"))
    except Exception as e:
        print(f"❌ Error running squeue: {e}")

    # Test sinfo
    print_section("Testing sinfo (Cluster Info)")
    try:
        result = sinfo()
        if result["status"] == "success":
            print("✅ sinfo successful:")
            print(result["data"])
        else:
            print("❌ sinfo failed:")
            print(result.get("error", "Unknown error"))
    except Exception as e:
        print(f"❌ Error running sinfo: {e}")

    print_section("Demo Complete")
    print("If you saw successful results above, your SLURM MCP server is working!")
    print("You can now use it with MCP clients to interact with your SLURM cluster.")


if __name__ == "__main__":
    main()
