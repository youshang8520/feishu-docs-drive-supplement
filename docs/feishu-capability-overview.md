# Feishu Capability Overview

This document explains what the Feishu supplement can do today, what is partially implemented, and what still benefits from an outer chat or orchestration layer.

## 1. Scope of the package

This package is a cc-connect supplement focused on:
- Feishu Drive
- Feishu Upload
- Feishu Docs
- Feishu Sheets
- Feishu Bitable
- User authorization bootstrap

It is designed to:
- inherit Feishu config from cc-connect
- expose a CLI surface for direct/manual use
- expose an MCP surface for higher-level plugins or bots

## 2. Authorization model

### Inherited auth
The package inherits app credentials and an optional tenant token from cc-connect config. Users do not need to supply a second config system.

### User auth bootstrap
The package supports a user-authorization flow with:
- `auth.start` to generate a verification link
- `auth.poll` to complete authorization and persist refresh/access tokens

This enables a low-friction flow for both direct CLI usage and higher-level chat integrations.

### What this package does not do by itself
This repo does not include:
- a standalone inbound chat server
- a hosted webhook runtime
- multi-user session orchestration


## 3. Current capability matrix

### Drive
Implemented:
- list folder contents
- create folder
- read file metadata
- move file/folder by target folder token
- delete node

Partially implemented:
- `drive.update` is reliable for move semantics

Not yet confirmed:
- stable rename support

### Upload
Implemented:
- upload local file
- upload bytes

### Docs
Implemented:
- create document
- read document metadata
- list blocks
- append plain text
- append headings
- append bullet blocks
- append simple styled text runs
- delete document
- update a known block's text using block id

Partially implemented:
- `docs.update` without `block_id` still behaves like append

Not yet implemented:
- precise block delete helper
- rich table/image abstraction helpers
- search/replace helper over arbitrary block trees
- full formatting abstraction layer

### Sheets
Implemented:
- create spreadsheet
- resolve sheet id
- read range
- write range
- append rows
- delete range / clear range

Not yet implemented:
- broader sheet metadata management
- row/column insertion helpers
- formatting/style helpers
- broader batch operations beyond current value flows

### Bitable
Implemented:
- list tables
- list fields
- create table
- read records
- create record
- update record
- delete record

Practical integration guidance:
- do not guess field names
- call `bitable.list_fields` first
- then construct `fields` for create/update

Not yet implemented:
- pagination controls as first-class user-facing options
- richer filter/sort passthrough
- batch record helpers

## 4. Low-friction integration target

The intended experience is:
1. user installs the supplement
2. config is inherited from cc-connect automatically
3. user runs `feishu-auth-setup`
4. the script generates the authorization link and displays it
5. user opens the link in browser and authorizes
6. the script automatically completes authorization
7. Feishu resource features become available

This repo provides the auth bootstrap, pending-auth persistence, and CLI/MCP entrypoints needed for that flow.

## 5. Current package positioning

The package should be described as:
- a reusable Feishu supplement for cc-connect
- with inherited auth/config
- with CLI and MCP entrypoints
- with strong Drive / Upload / Sheets / Bitable support
- with basic-to-mid-level Docs support
- not a full standalone hosted bot runtime

## 6. Practical recommendation

If published today, position the package as:
- a reusable supplement/backend layer
- suitable for direct CLI use and integration into a higher-level Feishu/cc-connect chat plugin
- intentionally non-invasive with respect to official cc-connect
