# Feishu Docs & Drive Supplement

[中文文档](README.zh-CN.md) | English

A Feishu supplement for cc-connect with inherited configuration, CLI and MCP entrypoints, a single-link user-authorization flow, and practical operations for Drive, Upload, Docs, Sheets, and Bitable.

## What this project provides

- Inherits Feishu app configuration from cc-connect.
- Exposes two entrypoints:
  - `feishu` CLI
  - `cc-feishu-mcp` MCP server
- Supports user authorization (handled by `feishu-auth-setup`)
- Provides practical support for:
  - Drive
  - Upload
  - Docs
  - Sheets
  - Bitable

## Install

```bash
pip install git+https://github.com/youshang8520/feishu-docs-drive-supplement.git
```

## One-click setup

```bash
feishu-auth-setup
```

This will:
1. Configure MCP plugin for Claude Code
2. Set up project-level MCP configuration
3. Guide you through authorization
4. Save tokens automatically

After setup, restart Claude Code and you can use Feishu features naturally in conversations.

## For advanced users

If you need manual control, you can use CLI commands directly:

```bash
# Check authorization status
feishu auth status

# List drive files
feishu drive list --folder root

# Create a document
feishu docs create --title "My Document"

# Append text to document
feishu docs append --doc <doc_token> --text "hello"
```

## Capability summary

### Included
- Drive: list / create-folder / read / move / delete
- Upload: file / bytes upload
- Docs: create / read / read-blocks / append / append-heading / append-bullet / append-styled / update / delete
- Sheets: create / read-range / write / append-rows / delete-range
- Bitable: list-tables / list-fields / create-table / read-records / create-record / update-record / delete-record
- Auth: inherited config + single-link auth bootstrap + pending-auth reuse

### Current boundaries
- Drive rename is not yet confirmed as a stable supported API shape.
- `docs.update` performs precise block-text updates when `block_id` is provided; without `block_id`, it falls back to append behavior.

## Documentation

- `README.feishu.md` — package overview and command surface
- `docs/feishu-capability-overview.md` — detailed capability matrix and positioning
- `docs/local-claude-import.md` — workspace integration notes
- `CHANGELOG.md` — release history

## Testing

```bash
pytest tests/test_validate.py tests/test_mcp_server.py
```
