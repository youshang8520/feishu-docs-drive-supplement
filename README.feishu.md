# Feishu Docs & Drive Supplement

A Python supplement package for cc-connect that adds Feishu Docs, Drive, Sheets, and Bitable capabilities with inherited configuration, CLI tooling, MCP tools, and user-authorization helpers.

## What this package does

- Inherits Feishu app configuration from an existing cc-connect config.
- Adds CLI and MCP entrypoints for Feishu resource operations.
- Supports a single-link user-authorization flow.
- Provides practical operations for:
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

## Configuration inheritance

**This supplement inherits cc-connect configuration by default; no manual setup required.**

Config is resolved in this order:

1. Environment variables
2. `CC_CONNECT_CONFIG_PATH`
3. `~/.cc-connect/config.toml`

Inherited Feishu keys are loaded from:

```toml
[[projects]]
name = "claudecode"

[[projects.platforms]]
type = "feishu"
[projects.platforms.options]
app_id = "..."
app_secret = "..."
tenant_access_token = "..."
# or token = "..."
base_url = "https://open.feishu.cn"
```

## Authorization flows

### CLI flow

Check current state:

```bash
python -m cc_feishu.cli auth status
```

Start auth and print the verification link:

```bash
python -m cc_feishu.cli auth start
```

Complete authorization after you approve:

```bash
python -m cc_feishu.cli auth poll --timeout 600
```

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
- `drive.create_folder`
- `drive.read`
- `drive.update`
- `drive.move`
- `drive.delete`
- `upload.bytes`

#### Docs / Sheets / Bitable
- `docs.create`
- `docs.read`
- `docs.read_blocks`
- `docs.append`
- `docs.append_heading`
- `docs.append_bullet`
- `docs.append_styled`
- `docs.update`
- `docs.delete`
- `sheets.create`
- `sheets.read_range`
- `sheets.write`
- `sheets.append_rows`
- `sheets.delete_range`
- `bitable.list_tables`
- `bitable.list_fields`
- `bitable.create_table`
- `bitable.read_records`
- `bitable.create_record`
- `bitable.update_record`
- `bitable.delete_record`

## Current boundaries

- `docs.update` supports precise block-text updates when a `block_id` is provided; without `block_id`, it falls back to append semantics.
- Docs support append helpers for headings, bullets, and simple styled text runs, but do not yet expose a full rich table/image abstraction layer.
- Drive rename is not yet confirmed as a stable supported API shape.
