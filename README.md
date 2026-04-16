# Feishu Docs & Drive Supplement

[中文文档](README.zh-CN.md) | English

A Feishu supplement for cc-connect, optimized for Claude Code. It reuses cc-connect credentials/configuration, exposes CLI and MCP entrypoints, provides a single-link user-authorization flow, and offers practical operations for Drive, Upload, Docs, Sheets, and Bitable.

## What this project provides

- Reuses Feishu app credentials/configuration from cc-connect.
- Is positioned as a Claude Code-oriented cc-connect supplement, not a standalone Feishu runtime.
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
- Adds direct-content tools so Claude can read folder contents, document bodies, sheet values, and bitable records without extra confirmation turns.

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
3. Register the Feishu MCP server in Claude Code project scope when `claude` is available
4. Guide you through authorization
5. Save tokens automatically

After setup, restart Claude Code and you can use Feishu features naturally in conversations.

**Examples:**
- "List my Feishu drive files"
- "Read this folder and tell me what files are inside"
- "Read the document at <url>"
- "Read this sheet: <url>"
- "Read this bitable view: <url>"
- "Create a document called Meeting Notes"

## For advanced users (CLI commands)

If you need manual control via terminal/command line, you can use CLI commands directly:

```bash
# Check authorization status
feishu auth status

# List drive files
feishu drive list --folder root

# Read folder contents directly
feishu drive read-folder --folder root

# Create a document
feishu docs create --title "My Document"

# Read document content directly
feishu docs read-content --doc <doc_token>

# Read sheet content directly
feishu sheets read-content --sheet <sheet_token> --range A1:C10

# Read bitable content directly
feishu bitable read-content --app <app_token> --table <table_id>
```

**Note:** These are terminal commands for developers and automation. Regular users should use Claude Code conversations instead.

## Capability summary

### Included
- Drive: list / read-folder / create-folder / read / move / delete
- Upload: file / bytes upload
- Docs: create / read / read-content / read-blocks / append / append-heading / append-bullet / append-styled / update / delete
- Sheets: create / read-range / read-content / write / append-rows / delete-range
- Bitable: list-tables / list-fields / create-table / read-records / read-content / create-record / update-record / delete-record
- Auth: inherited config + single-link auth bootstrap + pending-auth reuse

### Current boundaries
- Drive rename is not yet confirmed as a stable supported API shape.
- `docs.update` performs precise block-text updates when `block_id` is provided; without `block_id`, it falls back to append behavior.

## Documentation

- `README.feishu.md` — package overview and command surface
- `docs/feishu-capability-overview.md` — detailed capability matrix and positioning
- `docs/local-claude-import.md` — workspace integration notes
- `docs/mcp-auto-discovery.md` — Claude Code MCP registration and verification
- `CHANGELOG.md` — release history

## Testing

```bash
pytest
```
