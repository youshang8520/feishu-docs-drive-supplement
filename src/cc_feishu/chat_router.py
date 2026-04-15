from __future__ import annotations

import argparse
import json
import shlex
import time
from dataclasses import replace
from typing import Any

from .auth.token_provider import FeishuTokenProvider
from .cli import DEFAULT_AUTH_SCOPE
from .config import (
    PENDING_AUTH_FILE,
    USER_AUTH_FILE,
    clear_pending_auth_state,
    load_config,
    load_pending_auth_state,
    save_pending_auth_state,
    save_user_auth_state,
    validate_config,
)
from .errors import FeishuError, ValidationError
from .providers import init_provider
from .services.bitable import BitableService
from .services.docs import DocsService
from .services.drive import DriveService
from .services.messages import MessagesService
from .services.sheets import SheetsService
from .services.slides import SlidesService
from .services.upload import UploadService


class ChatCommandError(Exception):
    pass


class _ChatParser(argparse.ArgumentParser):
    def error(self, message):
        raise ChatCommandError(message)


def _auth_status(config: Any) -> dict[str, Any]:
    mode = config.auth_mode.strip().lower() or "auto"
    now = time.time()
    user_access_valid = bool(config.user_access_token.strip()) and now < config.user_token_expires_at - 60
    user_refresh_present = bool(config.user_refresh_token.strip())
    pending = load_pending_auth_state()
    pending_active = bool(pending.get("device_code")) and now < int(pending.get("expires_at", 0) or 0)
    return {
        "ok": True,
        "auth_mode": mode,
        "user_auth_file": str(USER_AUTH_FILE),
        "pending_auth_file": str(PENDING_AUTH_FILE),
        "has_app_credentials": bool(config.app_id and config.app_secret),
        "has_static_tenant_token": config.has_static_token,
        "has_user_access_token": bool(config.user_access_token.strip()),
        "has_user_refresh_token": user_refresh_present,
        "user_access_token_valid": user_access_valid,
        "user_token_expires_at": config.user_token_expires_at,
        "user_refresh_expires_at": config.user_refresh_expires_at,
        "user_open_id": config.user_open_id,
        "effective_auth": "user" if mode == "user" or (mode == "auto" and user_refresh_present) else "tenant",
        "has_pending_auth": pending_active,
        "pending_auth": pending if pending_active else None,
    }


def _pending_auth_response(pending: dict[str, Any]) -> dict[str, Any]:
    link = pending.get("verification_uri_complete") or pending.get("verification_uri")
    return {
        "ok": True,
        "status": "pending_authorization",
        "message": "Click the verification link to authorize Feishu access.",
        "reply": f"请点击授权链接完成飞书授权：{link}",
        "auth_mode": str(pending.get("auth_mode") or "user"),
        "scope": pending.get("scope") or DEFAULT_AUTH_SCOPE,
        "verification_uri": pending.get("verification_uri"),
        "verification_uri_complete": link,
        "user_code": pending.get("user_code"),
        "device_code": pending.get("device_code"),
        "expires_in": max(0, int(pending.get("expires_at", 0) or 0) - int(time.time())),
        "interval": pending.get("interval") or 5,
        "pending_auth_file": str(PENDING_AUTH_FILE),
    }




def _auth_message_text(pending: dict[str, Any], custom_text: str = "") -> str:
    link = str(pending.get("verification_uri_complete") or pending.get("verification_uri") or "").strip()
    if not link:
        raise ValidationError("verification link is missing")
    if custom_text.strip():
        return custom_text.strip().replace("{link}", link)
    return f"请点击链接完成飞书授权：{link}"


def _start_or_reuse_pending_auth(
    provider: FeishuTokenProvider,
    *,
    mode: str = "user",
    scope: str = DEFAULT_AUTH_SCOPE,
    force: bool = False,
) -> dict[str, Any]:
    pending = load_pending_auth_state()
    now = int(time.time())
    pending_active = bool(pending.get("device_code")) and now < int(pending.get("expires_at", 0) or 0)
    if pending_active and not force:
        return pending

    started = provider.start_device_authorization(scope)
    pending = {
        "auth_mode": mode,
        "scope": started.get("scope") or scope,
        "verification_uri": started.get("verification_uri"),
        "verification_uri_complete": started.get("verification_uri_complete") or started.get("verification_uri"),
        "user_code": started.get("user_code"),
        "device_code": started.get("device_code"),
        "interval": int(started.get("interval") or 5),
        "expires_in": int(started.get("expires_in") or 900),
        "expires_at": now + int(started.get("expires_in") or 900),
    }
    save_pending_auth_state(pending)
    return pending


def _send_auth_link(
    config: Any,
    provider: FeishuTokenProvider,
    receive_id: str,
    *,
    receive_id_type: str = "chat_id",
    custom_text: str = "",
    mode: str = "user",
    scope: str = DEFAULT_AUTH_SCOPE,
    force: bool = False,
) -> dict[str, Any]:
    pending = _start_or_reuse_pending_auth(provider, mode=mode, scope=scope, force=force)
    client = init_provider(config)
    messages = MessagesService(client)
    text = _auth_message_text(pending, custom_text)
    send_result = messages.send_text(receive_id, text, receive_id_type=receive_id_type)
    return {
        **_pending_auth_response(pending),
        "ok": True,
        "tool": "auth.send_link",
        "status": "pending_authorization",
        "message": "Sent Feishu authorization link.",
        "reply": text,
        "receive_id": receive_id,
        "receive_id_type": receive_id_type,
        "sent_message": send_result,
    }

def _build_parser() -> _ChatParser:
    parser = _ChatParser(prog="/feishu", add_help=False)
    sub = parser.add_subparsers(dest="resource")

    auth = sub.add_parser("auth", add_help=False)
    auth_sub = auth.add_subparsers(dest="action")
    auth_sub.add_parser("status", add_help=False)

    p = auth_sub.add_parser("start", add_help=False)
    p.add_argument("--scope", default=DEFAULT_AUTH_SCOPE)
    p.add_argument("--mode", default="user")
    p.add_argument("--force", action="store_true")

    p = auth_sub.add_parser("send-link", add_help=False)
    p.add_argument("--receive-id", required=True)
    p.add_argument("--receive-id-type", default="chat_id")
    p.add_argument("--text", default="")
    p.add_argument("--scope", default=DEFAULT_AUTH_SCOPE)
    p.add_argument("--mode", default="user")
    p.add_argument("--force", action="store_true")

    p = auth_sub.add_parser("poll", add_help=False)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--interval", type=int)
    p.add_argument("--device-code")
    p.add_argument("--mode", default="user")

    drive = sub.add_parser("drive", add_help=False)
    drive_sub = drive.add_subparsers(dest="action")
    p = drive_sub.add_parser("list", add_help=False)
    p.add_argument("--folder", required=True)
    p.add_argument("--page-token")
    p = drive_sub.add_parser("create-folder", add_help=False)
    p.add_argument("--parent", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--request-id")
    p = drive_sub.add_parser("read", add_help=False)
    p.add_argument("--file", required=True)
    p = drive_sub.add_parser("update", add_help=False)
    p.add_argument("--file", required=True)
    p.add_argument("--name")
    p.add_argument("--folder")
    p = drive_sub.add_parser("delete", add_help=False)
    p.add_argument("--token", required=True)
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--request-id")
    p = drive_sub.add_parser("move", add_help=False)
    p.add_argument("--token", required=True)
    p.add_argument("--target-folder", required=True)
    p.add_argument("--request-id")

    upload = sub.add_parser("upload", add_help=False)
    upload_sub = upload.add_subparsers(dest="action")
    p = upload_sub.add_parser("bytes", add_help=False)
    p.add_argument("--parent", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--mime", default="application/octet-stream")

    docs = sub.add_parser("docs", add_help=False)
    docs_sub = docs.add_subparsers(dest="action")
    p = docs_sub.add_parser("create", add_help=False)
    p.add_argument("--title", required=True)
    p.add_argument("--folder")
    p = docs_sub.add_parser("read", add_help=False)
    p.add_argument("--doc", required=True)
    p = docs_sub.add_parser("read-blocks", add_help=False)
    p.add_argument("--doc", required=True)
    p = docs_sub.add_parser("append", add_help=False)
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p = docs_sub.add_parser("append-heading", add_help=False)
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--level", type=int, choices=[1, 2], default=1)
    p.add_argument("--index", type=int)
    p = docs_sub.add_parser("append-bullet", add_help=False)
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--index", type=int)
    p = docs_sub.add_parser("append-styled", add_help=False)
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--bold", action="store_true")
    p.add_argument("--italic", action="store_true")
    p.add_argument("--underline", action="store_true")
    p.add_argument("--index", type=int)
    p = docs_sub.add_parser("update", add_help=False)
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--block")
    p = docs_sub.add_parser("delete", add_help=False)
    p.add_argument("--doc", required=True)

    sheets = sub.add_parser("sheets", add_help=False)
    sheets_sub = sheets.add_subparsers(dest="action")
    p = sheets_sub.add_parser("create", add_help=False)
    p.add_argument("--title", required=True)
    p.add_argument("--folder")
    p = sheets_sub.add_parser("read-range", add_help=False)
    p.add_argument("--sheet", required=True)
    p.add_argument("--range", required=True)
    p = sheets_sub.add_parser("write", add_help=False)
    p.add_argument("--sheet", required=True)
    p.add_argument("--range", required=True)
    p.add_argument("--values", required=True)
    p = sheets_sub.add_parser("append-rows", add_help=False)
    p.add_argument("--sheet", required=True)
    p.add_argument("--range", required=True)
    p.add_argument("--values", required=True)
    p = sheets_sub.add_parser("delete-range", add_help=False)
    p.add_argument("--sheet", required=True)
    p.add_argument("--range", required=True)

    bitable = sub.add_parser("bitable", add_help=False)
    bitable_sub = bitable.add_subparsers(dest="action")
    p = bitable_sub.add_parser("list-tables", add_help=False)
    p.add_argument("--app", required=True)
    p = bitable_sub.add_parser("list-fields", add_help=False)
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)
    p = bitable_sub.add_parser("create-table", add_help=False)
    p.add_argument("--app", required=True)
    p.add_argument("--name", required=True)
    p = bitable_sub.add_parser("read-records", add_help=False)
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--view")
    p = bitable_sub.add_parser("create-record", add_help=False)
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--fields", required=True)
    p = bitable_sub.add_parser("update-record", add_help=False)
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--record", required=True)
    p.add_argument("--fields", required=True)
    p = bitable_sub.add_parser("delete-record", add_help=False)
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--record", required=True)

    return parser



def _normalize_command(raw: str) -> list[str]:
    parts = shlex.split(raw)
    if not parts:
        raise ChatCommandError("empty command")
    head = parts[0].strip().lower()
    if head in {"/feishu", "feishu"}:
        parts = parts[1:]
    if not parts:
        raise ChatCommandError("missing feishu subcommand")
    return parts


def _auth_default(config: Any, provider: FeishuTokenProvider) -> dict[str, Any]:
    status = _auth_status(config)
    if status["effective_auth"] == "user" and status["user_access_token_valid"]:
        return {
            "ok": True,
            "status": "authorized",
            "tool": "auth.status",
            "message": "Feishu authorization is already active.",
            "reply": "飞书授权已生效，可以直接使用文档、云盘、表格和多维表格功能。",
            "result": status,
        }
    pending = _start_or_reuse_pending_auth(provider)
    return {
        "ok": True,
        "tool": "auth.start",
        **_pending_auth_response(pending),
    }


def route_command(command: str) -> dict[str, Any]:
    tokens = _normalize_command(command)
    parser = _build_parser()
    args = parser.parse_args(tokens)
    config = load_config()

    if args.resource == "auth" and args.action is None:
        provider = FeishuTokenProvider(config)
        try:
            return _auth_default(config, provider)
        except FeishuError as exc:
            return {"ok": False, "tool": "auth.start", "error": str(exc), "command": command}

    if args.resource == "auth":
        provider = FeishuTokenProvider(config)
        try:
            if args.action == "status":
                result = _auth_status(config)
                return {
                    "ok": True,
                    "tool": "auth.status",
                    "message": "Feishu authorization status fetched.",
                    "reply": "已获取飞书授权状态。",
                    "result": result,
                    "command": command,
                }
            if args.action == "start":
                pending = _start_or_reuse_pending_auth(
                    provider,
                    mode=args.mode,
                    scope=args.scope,
                    force=args.force,
                )
                return {
                    "ok": True,
                    "tool": "auth.start",
                    "command": command,
                    **_pending_auth_response(pending),
                }
            if args.action == "send-link":
                result = _send_auth_link(
                    config,
                    provider,
                    args.receive_id,
                    receive_id_type=args.receive_id_type,
                    custom_text=args.text,
                    mode=args.mode,
                    scope=args.scope,
                    force=args.force,
                )
                return {
                    **result,
                    "command": command,
                }
            if args.action == "poll":
                pending = load_pending_auth_state()
                device_code = (args.device_code or str(pending.get("device_code") or "")).strip()
                if not device_code:
                    raise ValidationError("device_code is required")
                result = provider.poll_device_authorization(
                    device_code,
                    interval_seconds=args.interval or int(pending.get("interval") or 5),
                    timeout_seconds=args.timeout,
                    auth_mode=args.mode,
                )
                clear_pending_auth_state()
                return {
                    "ok": True,
                    "tool": "auth.poll",
                    "command": command,
                    "message": f"Saved Feishu user auth into {USER_AUTH_FILE}",
                    "reply": "飞书授权已完成，现在可以直接使用补丁能力。",
                    "result": result,
                }
        except FeishuError as exc:
            return {"ok": False, "tool": f"auth.{args.action}", "error": str(exc), "command": command}

    errors = validate_config(config)
    if errors:
        return {"ok": False, "errors": errors, "command": command}

    client = init_provider(config)
    drive = DriveService(client)
    upload = UploadService(client)
    docs = DocsService(client)
    sheets = SheetsService(client)
    bitable = BitableService(client)

    try:
        result = None
        tool = None
        if args.resource == "drive":
            if args.action == "list":
                tool = "drive.list"
                result = drive.list_folder(args.folder, args.page_token)
            elif args.action == "create-folder":
                tool = "drive.create_folder"
                result = drive.create_folder(args.parent, args.name, args.request_id)
            elif args.action == "read":
                tool = "drive.read"
                result = drive.read_file_meta(args.file)
            elif args.action == "update":
                tool = "drive.update"
                result = drive.update_file_meta(args.file, name=args.name, folder_token=args.folder)
            elif args.action == "delete":
                tool = "drive.delete"
                result = drive.delete_node(args.token, recursive=args.recursive, request_id=args.request_id)
            elif args.action == "move":
                tool = "drive.move"
                result = drive.move_node(args.token, args.target_folder, request_id=args.request_id)
        elif args.resource == "upload" and args.action == "bytes":
            tool = "upload.bytes"
            result = upload.upload_bytes(args.parent, args.name, args.content.encode("utf-8"), mime=args.mime)
        elif args.resource == "docs":
            if args.action == "create":
                tool = "docs.create"
                result = docs.create(args.title, folder_token=args.folder)
            elif args.action == "read":
                tool = "docs.read"
                result = docs.read(args.doc)
            elif args.action == "read-blocks":
                tool = "docs.read_blocks"
                result = docs.list_blocks(args.doc)
            elif args.action == "append":
                tool = "docs.append"
                result = docs.append_text(args.doc, args.text)
            elif args.action == "append-heading":
                tool = "docs.append_heading"
                result = docs.append_heading(args.doc, args.text, level=args.level, index=args.index)
            elif args.action == "append-bullet":
                tool = "docs.append_bullet"
                result = docs.append_bullet(args.doc, args.text, index=args.index)
            elif args.action == "append-styled":
                tool = "docs.append_styled"
                result = docs.append_styled_text(
                    args.doc,
                    args.text,
                    bold=args.bold,
                    italic=args.italic,
                    underline=args.underline,
                    index=args.index,
                )
            elif args.action == "update":
                tool = "docs.update"
                result = docs.update_text(args.doc, args.text, block_id=args.block)
            elif args.action == "delete":
                tool = "docs.delete"
                result = docs.delete(args.doc)
        elif args.resource == "sheets":
            if args.action == "create":
                tool = "sheets.create"
                result = sheets.create(args.title, folder_token=args.folder)
            elif args.action == "read-range":
                tool = "sheets.read_range"
                result = sheets.read_range(args.sheet, args.range)
            elif args.action == "write":
                tool = "sheets.write"
                result = sheets.write_range(args.sheet, args.range, json.loads(args.values))
            elif args.action == "append-rows":
                tool = "sheets.append_rows"
                result = sheets.append_rows(args.sheet, args.range, json.loads(args.values))
            elif args.action == "delete-range":
                tool = "sheets.delete_range"
                result = sheets.delete_range(args.sheet, args.range)
        elif args.resource == "bitable":
            if args.action == "list-tables":
                tool = "bitable.list_tables"
                result = bitable.list_tables(args.app)
            elif args.action == "list-fields":
                tool = "bitable.list_fields"
                result = bitable.list_fields(args.app, args.table)
            elif args.action == "create-table":
                tool = "bitable.create_table"
                result = bitable.create_table(args.app, args.name)
            elif args.action == "read-records":
                tool = "bitable.read_records"
                result = bitable.read_records(args.app, args.table, view_id=args.view)
            elif args.action == "create-record":
                tool = "bitable.create_record"
                result = bitable.create_record(args.app, args.table, json.loads(args.fields))
            elif args.action == "update-record":
                tool = "bitable.update_record"
                result = bitable.update_record(args.app, args.table, args.record, json.loads(args.fields))
            elif args.action == "delete-record":
                tool = "bitable.delete_record"
                result = bitable.delete_record(args.app, args.table, args.record)
        if not tool:
            raise ChatCommandError("unsupported chat command")
        return {
            "ok": True,
            "tool": tool,
            "command": command,
            "message": f"Executed {tool}.",
            "reply": f"已执行 {tool}。",
            "result": result,
        }
    except (FeishuError, ValidationError, ValueError, ChatCommandError) as exc:
        return {
            "ok": False,
            "command": command,
            "error": str(exc),
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cc-feishu-chat", description="Feishu chat command router")
    parser.add_argument("command", help="raw chat command, for example: /feishu auth")
    args = parser.parse_args(argv)
    print(json.dumps(route_command(args.command), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
