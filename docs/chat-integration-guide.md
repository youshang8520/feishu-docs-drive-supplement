# Chat Integration Guide

This document explains how to integrate the Feishu supplement into an upper-layer chat or bot system so that end users can trigger authorization and Feishu operations from a conversation.

## 1. Integration boundary

This package is not a full chat bot by itself.
It provides:
- inherited cc-connect auth/config
- Feishu resource operations
- MCP tools for upper-layer integrations
- a single-link user authorization bootstrap
- a lightweight chat-command router (`cc-feishu-chat`) that parses fixed `/feishu ...` style commands and returns structured JSON responses
- a discoverable skill wrapper under `skills/feishu/SKILL.md` for runtimes that support workspace skill discovery

An outer chat integration is still responsible for:
- receiving inbound user messages or slash commands
- forwarding command text to `cc-feishu-chat` when embedding this package
- mapping users/sessions to follow-up behavior when running multi-user flows

## 2. Fixed command model

Suggested fixed commands:
- `/feishu auth`
- `/feishu auth start`
- `/feishu auth poll --timeout 600`
- `/feishu drive list --folder root`
- `/feishu docs append --doc <doc_token> --text "hello"`
- `/feishu docs update --doc <doc_token> --block <block_id> --text "updated text"`
- `/feishu docs append-heading --doc <doc_token> --text "Title" --level 1`
- `/feishu docs append-bullet --doc <doc_token> --text "Item"`
- `/feishu docs append-styled --doc <doc_token> --text "Important" --bold --italic`
- `/feishu bitable list-fields --app <app_token> --table <table_id>`

These commands can be passed directly to:

```bash
cc-feishu-chat "/feishu auth"
```

## 3. Authorization flow

### Option A — return the link and let the outer layer display it

Step 1 — user sends auth command:
- `/feishu auth`

Step 2 — outer layer calls chat router:

```bash
cc-feishu-chat "/feishu auth"
```

Step 3 — outer layer displays the returned link:
- the router returns structured JSON including `reply`, `verification_uri_complete`, and `status = pending_authorization`

Step 4 — after the user authorizes, outer layer completes polling:

```bash
cc-feishu-chat "/feishu auth poll --timeout 600"
```

## 4. Workspace skill compatibility path

If the host runtime supports workspace skill discovery, the repository includes:
- `skills/feishu/SKILL.md`

and a helper check script:
- `scripts/install_feishu_skill.py`

This path remains non-invasive:
- it does not modify official cc-connect core code
- it layers a `/feishu` wrapper over the supplement's own `cc-feishu-chat` entrypoint

Use the helper script to confirm the wrapper is present:

```bash
python scripts/install_feishu_skill.py
```

If the host runtime scans workspace `skills/`, refreshing or reopening the workspace should make `/feishu` discoverable.

## 5. Why this is compatible with official cc-connect

This design does not modify official cc-connect.
Instead it:
- inherits config from the same cc-connect config location
- exposes its own supplement entrypoints
- provides a wrapper skill and chat-router layer
- avoids coupling to official internal routing behavior

That means official cc-connect updates are much less likely to break the supplement, because the supplement is layered on top rather than patched into official code paths.

## 6. Router behavior recommendations

### Pending auth reuse
If the user repeats `/feishu auth`, call the same router command again. The supplement reuses pending auth automatically when still valid.

### User-facing replies
The outer layer should display:
- `reply` when present
- or `verification_uri_complete`
- or a fallback derived from `message`

### Error handling
If the router returns:
- `ok = false`
- display the error directly to the user or map it to a user-friendly message

## 7. Practical command examples

### Docs precise update
```bash
cc-feishu-chat "/feishu docs read-blocks --doc doc_token"
cc-feishu-chat "/feishu docs update --doc doc_token --block block_id --text 'updated text'"
```

### Docs richer append operations
```bash
cc-feishu-chat "/feishu docs append-heading --doc doc_token --text 'Title' --level 1"
cc-feishu-chat "/feishu docs append-bullet --doc doc_token --text 'Item'"
cc-feishu-chat "/feishu docs append-styled --doc doc_token --text 'Important' --bold --italic"
```

### Bitable schema-first workflow
```bash
cc-feishu-chat "/feishu bitable list-tables --app app_token"
cc-feishu-chat "/feishu bitable list-fields --app app_token --table table_id"
cc-feishu-chat "/feishu bitable update-record --app app_token --table table_id --record record_id --fields '{\"文本\":\"更新\"}'"
```

## 8. Current known boundaries

- Multi-user session orchestration is not implemented inside this repo.
- Drive rename remains an unresolved API-shape problem.
- Docs block deletion and richer table/image abstractions are not yet implemented.
