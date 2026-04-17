# Feishu Docs & Drive Supplement

A Python supplement package for cc-connect, optimized for Claude Code, that reuses cc-connect credentials/configuration and adds Feishu Docs, Drive, Sheets, and Bitable capabilities with CLI tooling, MCP tools, and user-authorization helpers.

## What this package does

- Reuses Feishu app credentials/configuration from an existing cc-connect setup.
- Is positioned as a Claude Code-oriented cc-connect supplement, not a standalone Feishu runtime.
- Adds CLI and MCP entrypoints for Feishu resource operations.
- Supports a single-link user-authorization flow.
- Provides practical operations for:
  - Drive
  - Upload
  - Docs
  - Sheets
  - Bitable
- Adds direct-content tools for reading folder contents, document bodies, sheet values, and bitable records.

## Install

```bash
pip install git+https://github.com/youshang8520/feishu-docs-drive-supplement.git
```

## One-click setup

```bash
feishu-auth-setup
```

Setup actions:
1. Configure MCP plugin for Claude Code
2. Set up project-level MCP configuration
3. Register the Feishu MCP server in Claude Code project scope when `claude` is available
4. Guide user authorization
5. Save tokens automatically

Restart Claude Code after setup.

**Examples:**
- "List my Feishu drive files"
- "Read this folder and tell me what files are inside"
- "Read the document at <url>"
- "Read this sheet: <url>"
- "Read this bitable view: <url>"

## CLI commands

Terminal / automation commands:

```bash
# Check current state
feishu auth status

# Read drive content
feishu drive list --folder root
feishu drive read-folder --folder root

# Create and read documents
feishu docs create --title "My Document"
feishu docs read-content --doc <doc_token>

# Read sheet / bitable content directly
feishu sheets read-content --sheet <sheet_token> --range A1:C10
feishu bitable read-content --app <app_token> --table <table_id>
```

**Note:** These terminal commands are intended for developers. Claude Code conversations remain supported through the MCP integration.

Successful user auth is persisted to `~/.cc-connect/feishu_user_auth.json`.

## Current capability surface

### CLI entrypoints
- `feishu auth ...`
- `feishu drive ...`
- `feishu upload ...`
- `feishu docs ...`
- `feishu sheets ...`
- `feishu slides ...`
- `feishu bitable ...`

### MCP tools
#### Auth
- `auth.status`
- `auth.start`
- `auth.poll`
- `auth.import`

#### Drive / Upload
- `drive.list`
- `drive.read_folder`
- `drive.create_folder`
- `drive.read`
- `drive.update`
- `drive.move`
- `drive.delete`
- `upload.bytes`

#### Docs / Sheets / Bitable
- `docs.create`
- `docs.read`
- `docs.read_content`
- `docs.read_blocks`
- `docs.append`
- `docs.append_heading`
- `docs.append_bullet`
- `docs.append_styled`
- `docs.update`
- `docs.delete`
- `sheets.create`
- `sheets.read_range`
- `sheets.read_content`
- `sheets.write`
- `sheets.append_rows`
- `sheets.delete_range`
- `bitable.list_tables`
- `bitable.list_fields`
- `bitable.create_table`
- `bitable.read_records`
- `bitable.read_content`
- `bitable.create_record`
- `bitable.update_record`
- `bitable.delete_record`

## Current boundaries

- `docs.update` supports precise block-text updates when a `block_id` is provided; without `block_id`, it falls back to append semantics.
- Docs support append helpers for headings, bullets, and simple styled text runs, but do not yet expose a full rich table/image abstraction layer.
- Drive rename is not yet confirmed as a stable supported API shape.
