# Changelog

## 0.1.0

### Added
- Feishu auth bootstrap with pending-auth reuse
- Direct auth-link delivery support for Feishu authorization flows
- Drive list/create/read/move/delete support
- Upload bytes support for plugin-style integrations
- Docs create/read/list-blocks/append/delete support
- Docs precise block text update support via `block_id`
- Sheets create/read/write/append/delete-range support
- Bitable list-tables/list-fields/create-table/read/create/update/delete support
- MCP tool surface for upper-layer bot/router integrations
- Capability overview, chat integration guide, and release documentation

### Changed
- Packaging metadata updated toward a generic GitHub-ready package shape
- Python 3.10 compatibility fixed with conditional `tomli` dependency
- Root ignore rules added for build artifacts and caches

### Known limitations
- Drive rename is not yet confirmed as a stable supported API shape
- Docs advanced formatting and block deletion are not fully implemented
- The package is not a standalone hosted chat runtime or multi-user session manager
