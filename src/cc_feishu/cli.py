from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from .auth.token_provider import FeishuTokenProvider
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

DEFAULT_AUTH_SCOPE = "offline_access drive:drive drive:file drive:file:upload space:folder:create sheets:spreadsheet bitable:app"


def _json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON argument: {exc}") from exc


def _print(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


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
        "message": "Open the verification URL and complete Feishu authorization.",
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="feishu", description="Feishu docs/drive supplement")
    parser.add_argument("--validate", action="store_true", help="validate env and connectivity")
    parser.add_argument("--dry-run", action="store_true", help="do not send write requests")

    sub = parser.add_subparsers(dest="resource")

    auth = sub.add_parser("auth")
    auth_sub = auth.add_subparsers(dest="action")

    auth_sub.add_parser("status")

    p = auth_sub.add_parser("import")
    p.add_argument("--refresh-token", required=True)
    p.add_argument("--access-token")
    p.add_argument("--expires-at", type=int, default=0)
    p.add_argument("--refresh-expires-at", type=int, default=0)
    p.add_argument("--open-id", default="")
    p.add_argument("--mode", choices=["auto", "user"], default="user")

    p = auth_sub.add_parser("login")
    p.add_argument("--scope", default=DEFAULT_AUTH_SCOPE)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--mode", choices=["auto", "user"], default="user")

    drive = sub.add_parser("drive")
    drive_sub = drive.add_subparsers(dest="action")

    p = drive_sub.add_parser("list")
    p.add_argument("--folder", required=True)
    p.add_argument("--page-token")

    p = drive_sub.add_parser("create-folder")
    p.add_argument("--parent", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--request-id")

    p = drive_sub.add_parser("read")
    p.add_argument("--file", required=True)

    p = drive_sub.add_parser("update")
    p.add_argument("--file", required=True)
    p.add_argument("--name")
    p.add_argument("--folder")

    p = drive_sub.add_parser("delete")
    p.add_argument("--token", required=True)
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--request-id")

    p = drive_sub.add_parser("move")
    p.add_argument("--token", required=True)
    p.add_argument("--target-folder", required=True)
    p.add_argument("--request-id")

    upload = sub.add_parser("upload")
    upload_sub = upload.add_subparsers(dest="action")

    p = upload_sub.add_parser("file")
    p.add_argument("--parent", required=True)
    p.add_argument("--path", required=True)
    p.add_argument("--name")

    p = upload_sub.add_parser("bytes")
    p.add_argument("--parent", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--mime", default="application/octet-stream")

    docs = sub.add_parser("docs")
    docs_sub = docs.add_subparsers(dest="action")

    p = docs_sub.add_parser("create")
    p.add_argument("--title", required=True)
    p.add_argument("--folder")

    p = docs_sub.add_parser("read-blocks")
    p.add_argument("--doc", required=True)

    p = docs_sub.add_parser("append")
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)

    p = docs_sub.add_parser("append-heading")
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--level", type=int, choices=[1, 2], default=1)
    p.add_argument("--index", type=int)

    p = docs_sub.add_parser("append-bullet")
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--index", type=int)

    p = docs_sub.add_parser("append-styled")
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--bold", action="store_true")
    p.add_argument("--italic", action="store_true")
    p.add_argument("--underline", action="store_true")
    p.add_argument("--index", type=int)

    p = docs_sub.add_parser("update")
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--block")

    p = docs_sub.add_parser("delete")
    p.add_argument("--doc", required=True)

    sheets = sub.add_parser("sheets")
    sheets_sub = sheets.add_subparsers(dest="action")

    p = sheets_sub.add_parser("create")
    p.add_argument("--title", required=True)
    p.add_argument("--folder")

    p = sheets_sub.add_parser("read-range")
    p.add_argument("--sheet", required=True)
    p.add_argument("--range", required=True)

    p = sheets_sub.add_parser("write")
    p.add_argument("--sheet", required=True)
    p.add_argument("--range", required=True)
    p.add_argument("--values", required=True)

    p = sheets_sub.add_parser("append-rows")
    p.add_argument("--sheet", required=True)
    p.add_argument("--range", required=True)
    p.add_argument("--values", required=True)

    p = sheets_sub.add_parser("delete-range")
    p.add_argument("--sheet", required=True)
    p.add_argument("--range", required=True)

    slides = sub.add_parser("slides")
    slides_sub = slides.add_subparsers(dest="action")

    p = slides_sub.add_parser("create")
    p.add_argument("--title", required=True)
    p.add_argument("--folder")

    p = slides_sub.add_parser("read")
    p.add_argument("--slides", required=True)

    p = slides_sub.add_parser("append-slide")
    p.add_argument("--slides", required=True)
    p.add_argument("--title", required=True)

    p = slides_sub.add_parser("update-slide")
    p.add_argument("--slides", required=True)
    p.add_argument("--slide", required=True)
    p.add_argument("--title", required=True)

    p = slides_sub.add_parser("delete-slide")
    p.add_argument("--slides", required=True)
    p.add_argument("--slide", required=True)

    bitable = sub.add_parser("bitable")
    bitable_sub = bitable.add_subparsers(dest="action")

    p = bitable_sub.add_parser("list-tables")
    p.add_argument("--app", required=True)

    p = bitable_sub.add_parser("create-table")
    p.add_argument("--app", required=True)
    p.add_argument("--name", required=True)

    p = bitable_sub.add_parser("list-fields")
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)

    p = bitable_sub.add_parser("read-records")
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--view")

    p = bitable_sub.add_parser("create-record")
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--fields", required=True)

    p = bitable_sub.add_parser("update-record")
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--record", required=True)
    p.add_argument("--fields", required=True)

    p = bitable_sub.add_parser("delete-record")
    p.add_argument("--app", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--record", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config = load_config()
    if args.dry_run:
        config = replace(config, dry_run=True)

    if args.validate:
        errors = validate_config(config)
        if errors:
            _print({"ok": False, "errors": errors})
            return 2
        client = init_provider(config)
        _print(client.validate_connectivity())
        return 0

    if not args.resource:
        parser.print_help()
        return 0

    if args.resource == "auth":
        provider = FeishuTokenProvider(config)
        try:
            if args.action == "status":
                _print(_auth_status(config))
            elif args.action == "import":
                updated = replace(
                    config,
                    auth_mode=args.mode,
                    user_access_token=(args.access_token or "").strip(),
                    user_refresh_token=args.refresh_token.strip(),
                    user_token_expires_at=args.expires_at,
                    user_refresh_expires_at=args.refresh_expires_at,
                    user_open_id=args.open_id.strip(),
                )
                save_user_auth_state(updated)
                _print(
                    {
                        "ok": True,
                        "message": f"Imported user auth into {USER_AUTH_FILE}",
                        "auth_mode": updated.auth_mode,
                        "has_user_refresh_token": bool(updated.user_refresh_token),
                        "has_user_access_token": bool(updated.user_access_token),
                        "user_open_id": updated.user_open_id,
                    }
                )
            elif args.action == "login":
                pending = _start_or_reuse_pending_auth(
                    provider,
                    mode=args.mode,
                    scope=args.scope,
                    force=False,
                )
                _print(_pending_auth_response(pending))
                result = provider.poll_device_authorization(
                    pending["device_code"],
                    interval_seconds=int(pending.get("interval") or args.interval),
                    timeout_seconds=args.timeout,
                    auth_mode=args.mode,
                )
                clear_pending_auth_state()
                _print(
                    {
                        "ok": True,
                        "status": "authorized",
                        "message": f"Saved Feishu user auth into {USER_AUTH_FILE}",
                        **result,
                    }
                )
            else:
                raise ValidationError("Unknown auth action")
            return 0
        except FeishuError as exc:
            _print({"ok": False, "error": str(exc)})
            return 1

    client = init_provider(config)
    drive = DriveService(client)
    upload = UploadService(client)
    docs = DocsService(client)
    sheets = SheetsService(client)
    slides = SlidesService(client)
    bitable = BitableService(client)

    try:
        if args.resource == "drive":
            if args.action == "list":
                _print(drive.list_folder(args.folder, args.page_token))
            elif args.action == "create-folder":
                _print(drive.create_folder(args.parent, args.name, args.request_id))
            elif args.action == "read":
                _print(drive.read_file_meta(args.file))
            elif args.action == "update":
                _print(drive.update_file_meta(args.file, name=args.name, folder_token=args.folder))
            elif args.action == "delete":
                _print(drive.delete_node(args.token, recursive=args.recursive, request_id=args.request_id))
            elif args.action == "move":
                _print(drive.move_node(args.token, args.target_folder, request_id=args.request_id))
            else:
                raise ValidationError("Unknown drive action")

        elif args.resource == "upload":
            if args.action == "file":
                p = Path(args.path)
                _print(upload.upload_file(args.parent, p, file_name=args.name))
            elif args.action == "bytes":
                _print(upload.upload_bytes(args.parent, args.name, args.content.encode("utf-8"), mime=args.mime))
            else:
                raise ValidationError("Unknown upload action")

        elif args.resource == "docs":
            if args.action == "create":
                _print(docs.create(args.title, folder_token=args.folder))
            elif args.action == "read":
                _print(docs.read(args.doc))
            elif args.action == "read-blocks":
                _print(docs.list_blocks(args.doc))
            elif args.action == "append":
                _print(docs.append_text(args.doc, args.text))
            elif args.action == "append-heading":
                _print(docs.append_heading(args.doc, args.text, level=args.level, index=args.index))
            elif args.action == "append-bullet":
                _print(docs.append_bullet(args.doc, args.text, index=args.index))
            elif args.action == "append-styled":
                _print(
                    docs.append_styled_text(
                        args.doc,
                        args.text,
                        bold=args.bold,
                        italic=args.italic,
                        underline=args.underline,
                        index=args.index,
                    )
                )
            elif args.action == "update":
                _print(docs.update_text(args.doc, args.text, block_id=args.block))
            elif args.action == "delete":
                _print(docs.delete(args.doc))
            else:
                raise ValidationError("Unknown docs action")

        elif args.resource == "sheets":
            if args.action == "create":
                _print(sheets.create(args.title, folder_token=args.folder))
            elif args.action == "read-range":
                _print(sheets.read_range(args.sheet, args.range))
            elif args.action == "write":
                _print(sheets.write_range(args.sheet, args.range, _json(args.values)))
            elif args.action == "append-rows":
                _print(sheets.append_rows(args.sheet, args.range, _json(args.values)))
            elif args.action == "delete-range":
                _print(sheets.delete_range(args.sheet, args.range))
            else:
                raise ValidationError("Unknown sheets action")

        elif args.resource == "slides":
            if args.action == "create":
                _print(slides.create(args.title, folder_token=args.folder))
            elif args.action == "read":
                _print(slides.read(args.slides))
            elif args.action == "append-slide":
                _print(slides.append_slide(args.slides, args.title))
            elif args.action == "update-slide":
                _print(slides.update_slide(args.slides, args.slide, args.title))
            elif args.action == "delete-slide":
                _print(slides.delete_slide(args.slides, args.slide))
            else:
                raise ValidationError("Unknown slides action")

        elif args.resource == "bitable":
            if args.action == "list-tables":
                _print(bitable.list_tables(args.app))
            elif args.action == "list-fields":
                _print(bitable.list_fields(args.app, args.table))
            elif args.action == "create-table":
                _print(bitable.create_table(args.app, args.name))
            elif args.action == "read-records":
                _print(bitable.read_records(args.app, args.table, view_id=args.view))
            elif args.action == "create-record":
                _print(bitable.create_record(args.app, args.table, _json(args.fields)))
            elif args.action == "update-record":
                _print(bitable.update_record(args.app, args.table, args.record, _json(args.fields)))
            elif args.action == "delete-record":
                _print(bitable.delete_record(args.app, args.table, args.record))
            else:
                raise ValidationError("Unknown bitable action")

        return 0
    except FeishuError as exc:
        _print({"ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
