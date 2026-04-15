# Local Import Guide for Claude/cc-connect

[English](local-claude-import.md) | [中文](local-claude-import.zh-CN.md)

## 1. Installation

```bash
python -m pip install -e .
```

## 2. Configuration Inheritance

This supplement inherits Feishu configuration from cc-connect by default; no separate configuration required.

Resolution order:

1. Environment variables
2. `config.toml` pointed to by `CC_CONNECT_CONFIG_PATH`
3. `~/.cc-connect/config.toml`

Expected Feishu configuration location:

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
```

## 3. Environment Variables

To override inherited values, explicitly set:

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_TENANT_ACCESS_TOKEN`
- `FEISHU_BASE_URL`
- `FEISHU_TIMEOUT_SECONDS`
- `FEISHU_DRY_RUN`
- `FEISHU_AUTH_MODE`
- `FEISHU_USER_ACCESS_TOKEN`
- `FEISHU_USER_REFRESH_TOKEN`
- `FEISHU_USER_TOKEN_EXPIRES_AT`
- `FEISHU_USER_REFRESH_EXPIRES_AT`
- `FEISHU_USER_OPEN_ID`

Notes:

- If you have a stable token, set `FEISHU_TENANT_ACCESS_TOKEN` directly
- Without a static token, you must provide `FEISHU_APP_ID` and `FEISHU_APP_SECRET`
- User authorization state is written to `~/.cc-connect/feishu_user_auth.json`
- Pending authorization state is written to `~/.cc-connect/feishu_pending_auth.json`

## 4. Quick Validation

```bash
feishu --validate
```

## 5. Authorization

Run the one-click setup:

```bash
feishu-auth-setup
```

This will automatically:
1. Generate authorization link
2. Display the link for you to open in browser
3. Wait for authorization completion
4. Save tokens to `~/.cc-connect/feishu_user_auth.json`

## 6. Plugin Resource Call Recommendations

Common MCP call examples:

```bash
cc-feishu-mcp drive.list --payload '{"folder_token":"root"}'
cc-feishu-mcp docs.append --payload '{"doc_token":"doc_token","text":"hello"}'
cc-feishu-mcp sheets.write --payload '{"sheet_token":"sheet_token","range":"A1:B2","values":[["a","b"]]}'
cc-feishu-mcp bitable.list_fields --payload '{"app_token":"app","table_id":"tbl"}'
cc-feishu-mcp bitable.update_record --payload '{"app_token":"app","table_id":"tbl","record_id":"rec","fields":{"Text":"Updated"}}'
cc-feishu-mcp upload.bytes --payload '{"parent_token":"folder","name":"note.md","content":"# hello","mime":"text/markdown"}'
```

For Bitable integration, don't guess field names. Recommended order:

1. `bitable.list_tables`
2. `bitable.list_fields`
3. `bitable.read_records`
4. `bitable.create_record` / `bitable.update_record`

## 7. Dry Run Example

```bash
feishu --dry-run drive create-folder --parent <folder_token> --name demo
```

## 8. Real Integration Status

Currently completed in real environment:

- Sheets: create / read / write / append / delete-range
- Bitable: list / list-fields / create / read / update / delete

Currently prioritizing user auth for:

- Drive
- Upload
- Sheets
- Bitable

To reproduce minimal Bitable CRUD connectivity verification, use empty field object on writable table:

```bash
feishu bitable create-record --app <app_token> --table <table_id> --fields '{}'
feishu bitable list-fields --app <app_token> --table <table_id>
```

## 9. Current Known Boundaries

- `docs.update` currently implements "append text" compatibility, not block-level overwrite
- Drive `update` reliable capability is moving by `folder_token`; rename API shape not yet stably confirmed
- Docs / Slides not yet forced to user auth, as device flow docs scopes still have compatibility limitations
