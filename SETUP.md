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

### One-click setup (Recommended)

```bash
feishu-auth-setup
```

This will:
1. Check your configuration
2. Set up MCP server (if using Claude Desktop)
3. Install workspace skill
4. Guide you through authorization

### Manual authorization

```bash
# Check status
feishu auth status

# Start authorization
feishu auth start

# Open the displayed link in your browser and authorize

# Complete authorization
feishu auth poll --timeout 600
```

## Verify Installation

```bash
# Test CLI
feishu auth status

# Test MCP server
cc-feishu-mcp auth.status --payload '{}'

# Test chat router
cc-feishu-chat "/feishu auth"
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

If you're using cc-connect with skill support, the `/feishu` command will be available after installation:

```
/feishu auth
/feishu drive list --folder root
/feishu docs read-blocks --doc <doc_token>
```

The skill is automatically installed at `skills/feishu/SKILL.md` by `feishu-auth-setup`.

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
3. Try force refresh:
   ```bash
   feishu auth start --force
   ```

### MCP server not working in Claude Desktop

1. Verify the command works:
   ```bash
   cc-feishu-mcp auth.status --payload '{}'
   ```

2. Check Claude Desktop logs for errors

3. Make sure the config file syntax is correct (valid JSON)

## Next Steps

- See `docs/feishu-capability-overview.md` for full capability list
- See `docs/mcp-configuration.md` for detailed MCP setup
- See `docs/chat-integration-guide.md` for integration patterns
