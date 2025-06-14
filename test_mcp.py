#!/usr/bin/env python3
"""Test script for the Hyper MCP server."""

import json
import subprocess
import sys


def test_mcp_server():
    """Test the MCP server functionality."""
    print("Testing Hyper MCP Server...")

    # Test 1: List tools
    print("\n1. Testing tools/list...")
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }

    try:
        # Run the MCP server
        process = subprocess.Popen(
            [sys.executable, "-c", "from hyper_cmd.mcp_server import main; main()"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send request
        stdout, stderr = process.communicate(json.dumps(request) + "\n")

        if stderr and "Plugin registry already initialized" not in stderr:
            print(f"Error: {stderr}")
            return False
        elif stderr:
            print(f"Note: {stderr}")

        response = json.loads(stdout.strip())

        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"✓ Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
        else:
            print(f"✗ Unexpected response: {response}")
            return False

    except Exception as e:
        print(f"✗ Error testing tools/list: {e}")
        return False

    # Test 2: Call a command (hello command for safe testing)
    print("\n2. Testing tools/call with hello command...")
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "hyper_hello",
            "arguments": {
                "name": "MCP Test"
            }
        }
    }

    try:
        process = subprocess.Popen(
            [sys.executable, "-c", "from hyper_cmd.mcp_server import main; main()"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(json.dumps(request) + "\n")

        if stderr:
            print(f"Note: {stderr}")

        response = json.loads(stdout.strip())

        if "result" in response:
            print("✓ Command execution test completed")
            if "isError" in response["result"]:
                print(f"  Command result: {response['result']}")
            else:
                print(f"  Success: {response['result']}")
        else:
            print(f"✗ Unexpected response: {response}")
            return False

    except Exception as e:
        print(f"✗ Error testing tools/call: {e}")
        return False

    print("\n✓ MCP Server tests completed successfully!")
    return True


def test_invalid_request():
    """Test error handling with invalid request."""
    print("\n3. Testing error handling...")
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "invalid/method",
        "params": {}
    }

    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "hyper_cmd.mcp_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(json.dumps(request) + "\n")
        response = json.loads(stdout.strip())

        if "error" in response or ("result" in response and "error" in response["result"]):
            print("✓ Error handling works correctly")
            if "error" in response:
                print(f"  Error: {response['error']}")
            else:
                print(f"  Error: {response['result']['error']}")
        else:
            print(f"✗ Expected error response, got: {response}")
            return False

    except Exception as e:
        print(f"✗ Error testing error handling: {e}")
        return False

    return True


def test_interactive_filtering():
    """Test that interactive commands are properly filtered."""
    print("\n4. Testing interactive command filtering...")

    try:
        from hyper_cmd.cli import discover_commands
        from hyper_cmd.mcp_server import MCPServer

        server = MCPServer()
        discover_commands()

        filtered_tools = server.get_tools()
        filtered_commands = {tool['name'][6:] for tool in filtered_tools}

        # All non-interactive commands should be present
        expected_commands = {'init', 'hello', 'test', 'testinfo'}  # Known safe commands
        missing_commands = expected_commands - filtered_commands

        if missing_commands:
            print(f"✗ Missing expected commands: {missing_commands}")
            return False

        # Test that the init command uses force flag automatically
        init_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "hyper_init",
                "arguments": {}
            }
        }

        # This should work without prompting for user input
        response = server.handle_request(init_request)
        if "error" in response or ("result" in response and "isError" in response["result"]):
            print(f"✗ Init command failed: {response}")
            return False

        print("✓ Interactive command filtering works correctly")
        print(f"  Available commands: {sorted(filtered_commands)}")
        print(f"  Total filtered commands: {len(filtered_commands)}")

        return True

    except Exception as e:
        print(f"✗ Error testing interactive filtering: {e}")
        return False


def test_mcp_resources():
    """Test MCP resources for command information."""
    print("\n5. Testing MCP resources...")

    try:
        from hyper_cmd.mcp_server import MCPServer

        server = MCPServer()

        # Test resources/list
        resources_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/list",
            "params": {}
        }

        response = server.handle_request(resources_request)
        if "error" in response or "resources" not in response.get("result", {}):
            print(f"✗ Resources list failed: {response}")
            return False

        resources = response["result"]["resources"]
        expected_resources = ["hyper://commands/available", "hyper://commands/interactive", "hyper://commands/all"]

        for expected_uri in expected_resources:
            if not any(r["uri"] == expected_uri for r in resources):
                print(f"✗ Missing expected resource: {expected_uri}")
                return False

        print(f"✓ Found {len(resources)} resources")

        # Test reading the "all commands" resource
        read_request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "resources/read",
            "params": {"uri": "hyper://commands/all"}
        }

        response = server.handle_request(read_request)
        if "error" in response or "contents" not in response.get("result", {}):
            print(f"✗ Resource read failed: {response}")
            return False

        content = json.loads(response["result"]["contents"][0]["text"])
        if "summary" not in content:
            print(f"✗ Resource content missing summary: {content}")
            return False

        summary = content["summary"]
        print(f"✓ Resource content valid - {summary['total_commands']} total commands")

        # Test reading interactive commands resource
        interactive_request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "resources/read",
            "params": {"uri": "hyper://commands/interactive"}
        }

        response = server.handle_request(interactive_request)
        if "error" in response:
            print(f"✗ Interactive resource read failed: {response}")
            return False

        interactive_content = json.loads(response["result"]["contents"][0]["text"])
        print(f"✓ Interactive commands resource: {interactive_content['count']} filtered commands")

        return True

    except Exception as e:
        print(f"✗ Error testing MCP resources: {e}")
        return False


def test_mcp_init_command():
    """Test the mcp-init command via MCP."""
    print("\n6. Testing mcp-init command...")

    try:
        import os
        import tempfile

        from hyper_cmd.mcp_server import MCPServer

        server = MCPServer()

        # Test the mcp-init command execution via MCP
        with tempfile.TemporaryDirectory() as tmp_dir:
            request = {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "hyper_mcp-init",
                    "arguments": {
                        "force": True,
                        "config_path": tmp_dir
                    }
                }
            }

            response = server.handle_request(request)

            if "error" in response or ("result" in response and "isError" in response["result"]):
                print(f"✗ mcp-init command failed: {response}")
                return False

            # Check if .mcp.json was created
            mcp_file = os.path.join(tmp_dir, ".mcp.json")
            if not os.path.exists(mcp_file):
                print("✗ .mcp.json file not created")
                return False

            # Verify file content
            with open(mcp_file) as f:
                content = f.read()

            if "hyper-core" not in content or "hyper-mcp" not in content:
                print("✗ .mcp.json missing expected configuration")
                return False

            print("✓ mcp-init command executed successfully")
            print("✓ .mcp.json created with correct configuration")

            # Test that the tool is listed in available tools
            tools = server.get_tools()
            mcp_init_tool = next((t for t in tools if t["name"] == "hyper_mcp-init"), None)

            if not mcp_init_tool:
                print("✗ mcp-init tool not found in available tools")
                return False

            print("✓ mcp-init tool properly exposed via MCP")

            return True

    except Exception as e:
        print(f"✗ Error testing mcp-init command: {e}")
        return False


if __name__ == "__main__":
    success = (test_mcp_server() and
               test_invalid_request() and
               test_interactive_filtering() and
               test_mcp_resources() and
               test_mcp_init_command())
    sys.exit(0 if success else 1)
