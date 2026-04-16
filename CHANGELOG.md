# Changelog

## 0.1.0

### Added
- Feishu auth bootstrap with pending-auth reuse
- Direct auth-link delivery support for Feishu authorization flows
- Drive list/create/read/move/delete support
- Direct-content drive folder reading via `drive.read_folder`
- Upload bytes support for plugin-style integrations
- Docs create/read/list-blocks/append/delete support
- Direct document body reading via `docs.read_content`
- Docs precise block text update support via `block_id`
- Sheets create/read/write/append/delete-range support
- Direct sheet value reading via `sheets.read_content`
- Bitable list-tables/list-fields/create-table/read/create/update/delete support
- Direct bitable record reading via `bitable.read_content`
- MCP tool surface for upper-layer bot/router integrations
- Capability overview, chat integration guide, and release documentation

### Changed
- Packaging metadata updated toward a generic GitHub-ready package shape
- Python 3.10 compatibility fixed with conditional `tomli` dependency
- Root ignore rules added for build artifacts and caches
- Release docs updated to match current MCP registration and direct-content behavior
- Docs write flow now supports `docs.append_code` and `docs.append_rich_text` across service, CLI, chat router, MCP server, manifest, and tool schemas
- Rich Feishu document output now defaults toward structured rich text, with command/config examples written as code blocks and batched appends used to reduce block-order corruption

### Known limitations
- Drive rename is not yet confirmed as a stable supported API shape
- Docs advanced formatting and block deletion are not fully implemented
- The package is not a standalone hosted chat runtime or multi-user session manager
