# Feishu Docs & Drive Supplement

A Feishu supplement for cc-connect with inherited configuration, CLI/MCP/chat entrypoints, a single-link user-authorization flow, and practical operations for Drive, Upload, Docs, Sheets, and Bitable.

## What this project provides

- Inherits Feishu app configuration from cc-connect.
- Exposes three entrypoints:
  - `feishu` CLI
  - `cc-feishu-mcp` MCP server
  - `cc-feishu-chat` fixed-command router
- Supports user authorization with:
  - `auth status`
  - `auth start`
  - `auth send-link`
  - `auth poll`
  - `auth import`
- Can send the authorization link directly into a Feishu chat when `receive_id` is provided.
- Provides practical support for:
  - Drive
  - Upload
  - Docs
  - Sheets
  - Bitable

## Install

```bash
python -m pip install -e .
```

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

Send the authorization link directly to a Feishu user or chat:

```bash
python -m cc_feishu.cli auth send-link --receive-id <target> --receive-id-type open_id
```

Complete polling after the user authorizes:

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
- Auth: inherited config + single-link auth bootstrap + pending-auth reuse + direct auth-link delivery

### Current boundaries
- Drive rename is not yet confirmed as a stable supported API shape.
- `docs.update` performs precise block-text updates when `block_id` is provided; without `block_id`, it falls back to append behavior.
- The project provides a fixed command router and direct auth-link delivery helper, but it is not a full long-running bot or webhook runtime.

## Documentation

- `README.feishu.md` — package overview and command surface
- `docs/feishu-capability-overview.md` — detailed capability matrix and positioning
- `docs/chat-integration-guide.md` — how to connect `/feishu ...` style commands to this package
- `docs/local-claude-import.md` — workspace integration notes
- `CHANGELOG.md` — release history

## Packaging artifacts

Prepared release artifacts are available in `github_publish/`.

## Testing

```bash
pytest tests/test_validate.py tests/test_chat_router.py tests/test_mcp_server.py
```
