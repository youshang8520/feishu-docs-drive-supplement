# Setup Guide

## Prerequisites

1. **cc-connect installed and configured**
   - Config file at: `~/.cc-connect/config.toml`
   - Must include Feishu app credentials
   - This package reuses cc-connect credentials and is not positioned as a standalone Feishu runtime

2. **Python 3.10+**

3. **`claude` CLI (optional but recommended)**
   - Used for automatic MCP registration in Claude Code
   - If unavailable, setup continues and only skips Claude MCP registration

## Installation

```bash
pip install -e .
```

## Configuration

### Option 1: Use existing cc-connect config (Recommended)

Existing cc-connect Feishu credentials are inherited automatically.

Your `~/.cc-connect/config.toml` should look like:

```toml
[[projects]]
  name = "claudecode"
  
  [[projects.platforms]]
    type = "feishu"
    [projects.platforms.options]
      app_id = "cli_xxxxxxxxxxxx"
      app_secret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Option 2: Use environment variables

Copy `.env.feishu.example` to `.env` and fill in your credentials:

```bash
cp .env.feishu.example .env
```

Edit `.env`:
```bash
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Authorization

Run the one-click setup:

```bash
feishu-auth-setup
```

Setup actions:
1. Check cc-connect-hosted credential configuration
2. Set up MCP plugin for Claude Code
3. Set up project-level MCP configuration
4. Register the Feishu MCP server in Claude Code project scope when `claude` is available
5. Guide user authorization
6. Save tokens automatically

When `claude` is unavailable, setup skips Claude MCP registration.
When cc-connect credentials are missing, setup stops with a clear message because this package reuses cc-connect credentials rather than replacing them.

Restart Claude Code after setup.

## Verify Installation

```bash
# Run one-click setup first
feishu-auth-setup

# Test CLI
feishu auth status

# Test MCP server
cc-feishu-mcp auth.status --payload '{}'

# Verify Claude Code project registration
claude mcp get feishu
```

Expected registration output should show `feishu` connected with `cc-feishu-mcp` as the command.

## Natural-language examples

Example prompts:
- "List my Feishu drive files"
- "Read this folder and tell me what files are inside"
- "Read the document at <url>"
- "Read this sheet: <url>"
- "Read this bitable view: <url>"
- "Create a document called 'Meeting Notes'"

These map to higher-level tools like `drive.read_folder`, `docs.read_content`, `sheets.read_content`, and `bitable.read_content`.

## Claude Desktop Integration

### Configure MCP Server

Edit your Claude Desktop config file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add:
```json
{
  "mcpServers": {
    "feishu": {
      "command": "cc-feishu-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

Restart Claude Desktop.

### Using in Claude Desktop

Example prompts:
- "List my Feishu drive files"
- "Read the document at <url>"
- "Read this sheet: <url>"
- "Create a document called 'Meeting Notes'"

Feishu MCP tools are then available in Claude Desktop.

## Troubleshooting

### "Command not found: cc-feishu-mcp"

Install the package:
```bash
pip install -e .
```

Python scripts directory must be in PATH.

### "Missing app_id or app_secret"

Check your configuration:
```bash
feishu --validate
```

Make sure either:
- `~/.cc-connect/config.toml` has Feishu credentials, OR
- Environment variables are set

### "Authorization failed"

1. Check your app credentials are correct
2. Make sure your Feishu app has the required scopes
3. Re-run `feishu-auth-setup`

### MCP server not working in Claude Code

1. Verify the command works:
   ```bash
   cc-feishu-mcp auth.status --payload '{}'
   ```

2. Verify Claude Code registered the project server:
   ```bash
   claude mcp get feishu
   ```

3. Check `.mcp.json` or `.claude/mcp.json` syntax is correct (valid JSON)

4. Restart Claude Code after running `feishu-auth-setup`

## Next Steps

- See `docs/feishu-capability-overview.md` for detailed capability matrix
- See `docs/local-claude-import.md` for workspace integration notes
- See `docs/mcp-auto-discovery.md` for MCP registration details
