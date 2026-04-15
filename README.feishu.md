# Feishu Docs & Drive Supplement

A Python supplement package for cc-connect that adds Feishu Docs, Drive, Sheets, and Bitable capabilities with inherited configuration, CLI tooling, MCP tools, user-authorization helpers, and a thin chat-command compatibility layer.

## What this package does

- Inherits Feishu app configuration from an existing cc-connect config.
- Adds CLI, MCP, and chat-router entrypoints for Feishu resource operations.
- Supports a single-link user-authorization flow.
- Can send the authorization link directly to a Feishu user or chat when a target `receive_id` is supplied.
- Provides practical operations for:
  - Drive
  - Upload
  - Docs
  - Sheets
  - Bitable

## Install

```bash
python -m pip install -e .
```

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

Send the authorization link directly into Feishu:

```bash
python -m cc_feishu.cli auth send-link --receive-id <target> --receive-id-type open_id
```

Complete authorization after the user approves:

```bash
python -m cc_feishu.cli auth poll --timeout 600
```

Successful user auth is persisted to `~/.cc-connect/feishu_user_auth.json`.

### Chat-router flow

For a higher-level chat or command host, the intended flow is:

```bash
cc-feishu-chat "/feishu auth"
cc-feishu-chat "/feishu auth send-link --receive-id <target> --receive-id-type open_id"
cc-feishu-chat "/feishu auth poll --timeout 600"
```

Behavior:
- `cc-feishu-chat "/feishu auth"` returns structured JSON including `verification_uri_complete`
- pending auth is cached locally and can be reused
- `auth send-link` can deliver the link directly to Feishu
- `poll` can resume without the caller resending `device_code`

## Slash-command compatibility path

This repository includes a thin workspace-skill wrapper at:
- `skills/feishu/SKILL.md`

and a helper script:
- `scripts/install_feishu_skill.py`

The wrapper is designed so a host that supports workspace skill discovery can expose `/feishu ...` without modifying official cc-connect source code.

The wrapper delegates to:

```bash
cc-feishu-chat "/feishu $ARGUMENTS"
```

This is the preferred compatibility path because it layers on top of the official runtime instead of patching official core code.

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
- `auth.send_link`
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

### Chat router
- `cc-feishu-chat`
  - parses fixed `/feishu ...` style commands
  - returns structured JSON for an outer chat layer
  - supports auth-link generation and auth-link delivery
  - provides a compatibility layer without modifying official cc-connect

## Current boundaries

- `docs.update` supports precise block-text updates when a `block_id` is provided; without `block_id`, it falls back to append semantics.
- Docs support append helpers for headings, bullets, and simple styled text runs, but do not yet expose a full rich table/image abstraction layer.
- Drive rename is not yet confirmed as a stable supported API shape.
- The package includes direct auth-link delivery and a fixed command router, but it is not a standalone long-running bot server or multi-user session manager.
