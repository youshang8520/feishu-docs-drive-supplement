# MCP Auto-Discovery

This package makes the Feishu MCP server discoverable to Claude Code after setup.

## How it works

1. **Installation**: When you run `pip install -e .`, the package registers an MCP entry point
2. **Auto-discovery**: Claude Code may discover the MCP server through Python's entry points depending on environment support
3. **Project config**: `feishu-auth-setup` creates `.claude/mcp.json` for project-level configuration
4. **Shared project config**: the repository can also include a top-level `.mcp.json` for shared project registration
5. **Claude registration**: `feishu-auth-setup` also runs `claude mcp add --scope project feishu -- cc-feishu-mcp` when the `claude` CLI is available

## Manual Configuration (if needed)

If auto-discovery doesn't work, you can manually configure:

### Project-level (Recommended)

Run the one-click setup first:

```bash
feishu-auth-setup
```

That command writes `.claude/mcp.json` and attempts to register the same server with:

```bash
claude mcp add --scope project feishu -- cc-feishu-mcp
```

If you need to create or edit `.claude/mcp.json` manually:
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

If you prefer shared repo config, `.mcp.json` can contain:
```json
{
  "mcpServers": {
    "feishu": {
      "type": "stdio",
      "command": "cc-feishu-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

### User-level (Global)

Edit Claude Desktop config:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the same configuration as above.

## Verification

After installation, run setup and restart Claude Code, then check:

```bash
# Register project MCP config and Claude MCP entry
feishu-auth-setup

# Test MCP server directly
cc-feishu-mcp auth.status --payload '{}'

# Inspect Claude MCP registration
claude mcp get feishu
```

You should see `feishu` connected to `cc-feishu-mcp`.

Typical tool names include:
- `mcp__feishu__auth.status`
- `mcp__feishu__drive.list`
- `mcp__feishu__drive.read_folder`
- `mcp__feishu__docs.read_content`
- `mcp__feishu__sheets.read_content`
- `mcp__feishu__bitable.read_content`

## Why the direct-content tools matter

The higher-level read tools cover common content retrieval scenarios such as:
- "这个文件夹里有什么"
- "这个文档说了啥"
- "看下这个表格内容"
- "看下这个多维表格数据"

They return normalized content-oriented results instead of exposing low-level raw API output.

## Troubleshooting

### MCP tools not showing up

1. **Restart Claude Code completely**
2. **Reopen the project directory**
3. **Run setup again**: `feishu-auth-setup`
4. **Check project config exists**: `.claude/mcp.json` or `.mcp.json`
5. **Verify command works**: `cc-feishu-mcp auth.status --payload '{}'`
6. **Verify Claude registration**: `claude mcp get feishu`

### "Command not found: cc-feishu-mcp"

Make sure Python scripts directory is in PATH:
```bash
# Windows
echo %PATH% | findstr Python

# macOS/Linux
echo $PATH | grep python
```

If not, add it or use full path in MCP config:
```json
{
  "mcpServers": {
    "feishu": {
      "command": "D:/Program Files/Python312/Scripts/cc-feishu-mcp",
      "args": []
    }
  }
}
```
