"""MCP server for Feishu integration."""

def get_server_info():
    """Return MCP server information for auto-discovery."""
    return {
        "command": "cc-feishu-mcp",
        "args": [],
        "env": {},
        "description": "Feishu Drive, Docs, Sheets, and Bitable operations",
    }

