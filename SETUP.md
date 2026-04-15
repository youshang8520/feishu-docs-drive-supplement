# Setup Guide

## Prerequisites

1. **cc-connect installed and configured**
   - Config file at: `~/.cc-connect/config.toml`
   - Must include Feishu app credentials

2. **Python 3.10+**

## Installation

```bash
pip install -e .
```

## Configuration

### Option 1: Use existing cc-connect config (Recommended)

If you already have cc-connect configured with Feishu credentials, the supplement will automatically inherit them.

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

This will:
1. Check your configuration
2. Set up MCP plugin for Claude Code
3. Set up project-level MCP configuration
4. Guide you through authorization
5. Save tokens automatically

After setup, restart Claude Code and you can use Feishu features naturally in conversations.

## Verify Installation

```bash
# Test CLI
feishu auth status

# Test MCP server
cc-feishu-mcp auth.status --payload '{}'
```

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

After setup, you can ask naturally:
- "List my Feishu drive files"
- "Create a document called 'Meeting Notes'"
- "Read the document at <url>"

Claude will automatically use the Feishu MCP tools.

## Workspace Skill (cc-connect)


```
```


## Troubleshooting

### "Command not found: cc-feishu-mcp"

Make sure the package is installed:
```bash
pip install -e .
```

And that your Python scripts directory is in PATH.

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
3. Try running `feishu-auth-setup` again

### MCP server not working in Claude Code

1. Verify the command works:
   ```bash
   cc-feishu-mcp auth.status --payload '{}'
   ```

2. Check Claude Desktop logs for errors

3. Make sure the config file syntax is correct (valid JSON)

## Next Steps

- See `docs/feishu-capability-overview.md` for detailed capability matrix
- See `docs/local-claude-import.md` for workspace integration notes
