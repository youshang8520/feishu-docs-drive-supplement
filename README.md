# Feishu Docs & Drive Supplement

[中文文档](README.zh-CN.md) | English

A Feishu supplement for cc-connect with inherited configuration, CLI and MCP entrypoints, a single-link user-authorization flow, and practical operations for Drive, Upload, Docs, Sheets, and Bitable.

## What this project provides

- Inherits Feishu app configuration from cc-connect.
- Exposes two entrypoints:
  - `feishu` CLI
  - `cc-feishu-mcp` MCP server
- Supports user authorization with:
  - `auth status`
  - `auth start`
  - `auth poll`
  - `auth import`
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

## Configuration

**This supplement inherits cc-connect configuration by default; no manual setup required.**

By default the package reuses Feishu configuration from cc-connect.

Resolution order:

1. Environment variables
2. `CC_CONNECT_CONFIG_PATH`
3. `~/.cc-connect/config.toml`

Expected config shape:

```toml
[[projects]]
name = "claudecode"

[[projects.platforms]]
type = "feishu"
[projects.platforms.options]
app_id = "..."
app_secret = "..."
tenant_access_token = "..."
base_url = "https://open.feishu.cn"
```

## Quick start

Check auth state:

```bash
python -m cc_feishu.cli auth status
```

Start authorization (generates link to open in browser):

```bash
python -m cc_feishu.cli auth start
```

Complete polling after you authorize:

```bash
python -m cc_feishu.cli auth poll --timeout 600
```

Example resource operations after authorization:

```bash
python -m cc_feishu.cli docs append --doc <doc_token> --text "hello"
python -m cc_feishu.cli drive list --folder root
python -m cc_feishu.cli bitable list-fields --app <app_token> --table <table_id>
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
