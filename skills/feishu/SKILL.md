---
name: feishu
description: Use this slash command to authorize Feishu access and operate Drive, Docs, Sheets, and Bitable through the supplement backend.
argument-hint: "[subcommand]"
allowed-tools: Bash, Read
category: Integration
version: 0.1.0
user-invocable: true
disable-model-invocation: false
homepage: https://github.com/example/feishu-docs-drive-supplement
metadata: {"openclaw":{"emoji":"📄","os":["win32","linux","darwin"],"requires":{"bins":["cc-feishu-chat"]},"homepage":"https://github.com/example/feishu-docs-drive-supplement"}}
---

# /feishu

This skill provides a cc-connect/OpenClaw-compatible slash-command entry for the Feishu supplement without modifying official cc-connect code.

## How it works

When the user invokes `/feishu ...`, execute the local chat-router entrypoint and return the structured result.

Use this exact pattern:

```bash
cc-feishu-chat "/feishu $ARGUMENTS"
```

If there are no arguments, use:

```bash
cc-feishu-chat "/feishu auth"
```

## Output handling

The command returns JSON.

Priority for user-visible output:
1. `reply`
2. `message`
3. compact JSON summary if neither exists

If `verification_uri_complete` is present, include it plainly in the reply so the user can click it.

If `ok` is false, report the error directly.

## Common commands

- `/feishu auth`
- `/feishu auth poll --timeout 600`
- `/feishu drive list --folder root`
- `/feishu docs read-blocks --doc <doc_token>`
- `/feishu docs update --doc <doc_token> --block <block_id> --text "updated text"`
- `/feishu docs append-heading --doc <doc_token> --text "Title" --level 1`
- `/feishu docs append-bullet --doc <doc_token> --text "Item"`
- `/feishu docs append-styled --doc <doc_token> --text "Important" --bold --italic`
- `/feishu bitable list-fields --app <app_token> --table <table_id>`

## Notes

- This skill is a thin compatibility wrapper over `cc-feishu-chat`.
- It does not modify official cc-connect internals.
- It depends on the package being installed and on the workspace skill discovery loading this `skills/feishu/SKILL.md` file.
