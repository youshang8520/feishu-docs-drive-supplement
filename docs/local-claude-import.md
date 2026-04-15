# 在 Claude/cc-connect 中本地导入说明

## 1. 安装

```bash
python -m pip install -e .
```

## 2. 配置继承

本补丁默认继承现有 cc-connect 的飞书配置，不要求你再维护一套独立配置。

读取顺序：

1. 环境变量
2. `CC_CONNECT_CONFIG_PATH` 指向的 `config.toml`
3. `~/.cc-connect/config.toml`

会从以下位置读取飞书配置：

```toml
[[projects]]
name = "claudecode"

[[projects.platforms]]
type = "feishu"
[projects.platforms.options]
app_id = "..."
app_secret = "..."
tenant_access_token = "..."
# 或 token = "..."
```

## 3. 环境变量

如需覆盖继承值，可显式设置：

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

说明：

- 已有稳定 token 时，可直接设置 `FEISHU_TENANT_ACCESS_TOKEN`
- 若没有静态 token，则必须提供 `FEISHU_APP_ID` 与 `FEISHU_APP_SECRET`
- 用户授权状态会写入 `~/.cc-connect/feishu_user_auth.json`
- 待完成授权状态会写入 `~/.cc-connect/feishu_pending_auth.json`

## 4. 快速验证

```bash
feishu --validate
```

## 5. MCP 单链接授权接入

如果你要在机器人/插件里做“发一条链接让用户点授权”，直接接这组命令即可：

```bash
cc-feishu-mcp auth.status --payload '{}'
cc-feishu-mcp auth.start --payload '{}'
cc-feishu-mcp auth.poll --payload '{"timeout":600}'
```

推荐接法：

1. 调 `auth.start`
2. 把返回的 `verification_uri_complete` 发给用户
3. 用户点完后，后台调 `auth.poll`
4. 成功后用户 refresh token 自动落盘

补充说明：

- `auth.start` 会缓存 pending auth；未过期时重复调用会复用已有链接
- 如需强制刷新授权链接，可调用：

```bash
cc-feishu-mcp auth.start --payload '{"force": true}'
```

## 6. 插件资源调用建议

常用 MCP 调用示例：

```bash
cc-feishu-mcp drive.list --payload '{"folder_token":"root"}'
cc-feishu-mcp docs.append --payload '{"doc_token":"doc_token","text":"hello"}'
cc-feishu-mcp sheets.write --payload '{"sheet_token":"sheet_token","range":"A1:B2","values":[["a","b"]]}'
cc-feishu-mcp bitable.list_fields --payload '{"app_token":"app","table_id":"tbl"}'
cc-feishu-mcp bitable.update_record --payload '{"app_token":"app","table_id":"tbl","record_id":"rec","fields":{"文本":"更新"}}'
cc-feishu-mcp upload.bytes --payload '{"parent_token":"folder","name":"note.md","content":"# hello","mime":"text/markdown"}'
```

Bitable 接入不要先猜字段名，推荐顺序：

1. `bitable.list_tables`
2. `bitable.list_fields`
3. `bitable.read_records`
4. `bitable.create_record` / `bitable.update_record`

## 7. 干跑示例

```bash
feishu --dry-run drive create-folder --parent <folder_token> --name demo
```

## 8. 真实联调状态

当前已在真实环境完成：

- Sheets：create / read / write / append / delete-range
- Bitable：list / list-fields / create / read / update / delete

当前默认优先走 user auth 的能力：

- Drive
- Upload
- Sheets
- Bitable

如需复现 Bitable 的最小 CRUD 连通性验证，可先对可写表使用空字段对象：

```bash
feishu bitable create-record --app <app_token> --table <table_id> --fields '{}'
feishu bitable list-fields --app <app_token> --table <table_id>
```

## 9. 当前已知边界

- `docs.update` 当前仍是“追加文本”的兼容实现，不是块级覆盖更新
- Drive `update` 当前可靠能力是按 `folder_token` 移动；rename API 形态尚未稳定确认
- Docs / Slides 暂未强制切到 user auth，因为 device flow 下 docs scopes 仍存在兼容性限制
