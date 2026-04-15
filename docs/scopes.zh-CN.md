# Feishu 权限范围建议

[English](scopes.md) | 中文

为了完成本补丁要求的真实联调（Drive/Upload/Docs/Sheets/Bitable 的创建、读取、更新、删除），建议在飞书应用中开通以下最小权限。

## 1) Drive / Upload / Docs 删除相关

- `drive:drive`
- `space:folder:create`
- `drive:file`
- `drive:file:upload`
- `space:document:delete`

## 2) Docs（Docx）读写

- `docs:document:read`
- `docs:document:write`

> 说明：当前代码已使用 Docx blocks 接口完成追加/更新写入；若仅缺删除能力，主要补 `space:document:delete`。

## 3) Sheets（表格）

- `sheets:spreadsheet`
- `sheets:spreadsheet:create`
- `sheets:spreadsheet:read`（或对应 readonly）
- `drive:drive`（表格创建/访问依赖）

## 4) Bitable（多维表格）

- `bitable:app`
- `bitable:app:readonly`
- `base:table:read`
- `base:table:create`
- `base:record:retrieve`
- `base:record:create`
- `base:record:update`
- `base:record:delete`

## 5) 使用建议

- 按最小必要原则开通；如果只验证部分能力，只开对应 scope。
- scope 开通后，重新执行全量真实 CRUD 验证矩阵，再决定是否发布。
