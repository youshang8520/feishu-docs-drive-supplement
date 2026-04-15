# Feishu Permission Scopes Recommendation

[English](scopes.md) | [中文](scopes.zh-CN.md)

To complete the real integration required by this supplement (Drive/Upload/Docs/Sheets/Bitable create, read, update, delete), it is recommended to enable the following minimum permissions in your Feishu app.

## 1) Drive / Upload / Docs Deletion

- `drive:drive`
- `space:folder:create`
- `drive:file`
- `drive:file:upload`
- `space:document:delete`

## 2) Docs (Docx) Read/Write

- `docs:document:read`
- `docs:document:write`

> Note: Current code uses Docx blocks API for append/update writes; if only deletion capability is missing, mainly add `space:document:delete`.

## 3) Sheets (Spreadsheet)

- `sheets:spreadsheet`
- `sheets:spreadsheet:create`
- `sheets:spreadsheet:read` (or corresponding readonly)
- `drive:drive` (spreadsheet creation/access dependency)

## 4) Bitable (Multi-dimensional Table)

- `bitable:app`
- `bitable:app:readonly`
- `base:table:read`
- `base:table:create`
- `base:record:retrieve`
- `base:record:create`
- `base:record:update`
- `base:record:delete`

## 5) Usage Recommendations

- Enable based on minimum necessary principle; if only verifying partial capabilities, only enable corresponding scopes.
- After enabling scopes, re-run full real CRUD verification matrix before deciding to publish.
