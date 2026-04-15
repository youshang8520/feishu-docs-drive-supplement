from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from typing import Any

from ..auth.token_provider import FeishuTokenProvider
from ..cli import DEFAULT_AUTH_SCOPE
from ..config import (
    PENDING_AUTH_FILE,
    USER_AUTH_FILE,
    clear_pending_auth_state,
    load_config,
    load_pending_auth_state,
    save_pending_auth_state,
    save_user_auth_state,
    validate_config,
)
from ..errors import FeishuError, ValidationError
from ..providers import init_provider
from ..services.bitable import BitableService
from ..services.docs import DocsService
from ..services.drive import DriveService
from ..services.messages import MessagesService
from ..services.sheets import SheetsService
from ..services.slides import SlidesService
from ..services.upload import UploadService


def _print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


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


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cc-feishu-mcp", description="Feishu MCP bridge")
    p.add_argument("tool", help="tool name")
    p.add_argument("--payload", default="{}", help="json payload")
    return p


def _parse_payload(raw: str) -> dict:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("payload must be a json object")
    return data


def _pending_auth_response(config: Any, pending: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "pending_authorization",
        "message": "Open the verification URL and complete Feishu authorization.",
        "auth_mode": str(pending.get("auth_mode") or "user"),
        "scope": pending.get("scope") or DEFAULT_AUTH_SCOPE,
        "verification_uri": pending.get("verification_uri"),
        "verification_uri_complete": pending.get("verification_uri_complete") or pending.get("verification_uri"),
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
        **_pending_auth_response(config, pending),
        "ok": True,
        "status": "pending_authorization",
        "message": "Sent Feishu authorization link.",
        "receive_id": receive_id,
        "receive_id_type": receive_id_type,
        "sent_message": send_result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config = load_config()
    payload = _parse_payload(args.payload)
    tool = args.tool

    if tool.startswith("auth."):
        provider = FeishuTokenProvider(config)
        try:
            if tool == "auth.status":
                _print(_auth_status(config))
            elif tool == "auth.import":
                mode = str(payload.get("mode") or "user").strip() or "user"
                updated = replace(
                    config,
                    auth_mode=mode,
                    user_access_token=str(payload.get("access_token") or "").strip(),
                    user_refresh_token=str(payload.get("refresh_token") or "").strip(),
                    user_token_expires_at=int(payload.get("expires_at") or 0),
                    user_refresh_expires_at=int(payload.get("refresh_expires_at") or 0),
                    user_open_id=str(payload.get("open_id") or "").strip(),
                )
                save_user_auth_state(updated)
                clear_pending_auth_state()
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
            elif tool == "auth.start":
                mode = str(payload.get("mode") or "user").strip() or "user"
                scope = str(payload.get("scope") or DEFAULT_AUTH_SCOPE).strip() or DEFAULT_AUTH_SCOPE
                force = bool(payload.get("force") is True)
                pending = _start_or_reuse_pending_auth(provider, mode=mode, scope=scope, force=force)
                _print(_pending_auth_response(config, pending))
            elif tool == "auth.send_link":
                result = _send_auth_link(
                    config,
                    provider,
                    str(payload.get("receive_id") or "").strip(),
                    receive_id_type=str(payload.get("receive_id_type") or "chat_id"),
                    custom_text=str(payload.get("text") or ""),
                    mode=str(payload.get("mode") or "user").strip() or "user",
                    scope=str(payload.get("scope") or DEFAULT_AUTH_SCOPE).strip() or DEFAULT_AUTH_SCOPE,
                    force=bool(payload.get("force") is True),
                )
                _print(result)
            elif tool == "auth.poll":
                pending = load_pending_auth_state()
                device_code = str(payload.get("device_code") or pending.get("device_code") or "").strip()
                if not device_code:
                    raise ValidationError("device_code is required")
                result = provider.poll_device_authorization(
                    device_code,
                    interval_seconds=int(payload.get("interval") or pending.get("interval") or 5),
                    timeout_seconds=int(payload.get("timeout") or 600),
                    auth_mode=str(payload.get("mode") or pending.get("auth_mode") or "user").strip() or "user",
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
                _print({"ok": False, "error": f"unsupported tool: {tool}"})
                return 2
            return 0
        except FeishuError as exc:
            _print({"ok": False, "error": str(exc)})
            return 1

    errors = validate_config(config)
    if errors:
        _print({"ok": False, "errors": errors})
        return 2

    client = init_provider(config)

    drive = DriveService(client)
    upload = UploadService(client)
    docs = DocsService(client)
    sheets = SheetsService(client)
    slides = SlidesService(client)
    bitable = BitableService(client)

    result = None

    if tool == "drive.list":
        result = drive.list_folder(payload["folder_token"], payload.get("page_token"))
    elif tool == "drive.create_folder":
        result = drive.create_folder(payload["parent_token"], payload["name"], payload.get("request_id"))
    elif tool == "drive.read":
        result = drive.read_file_meta(payload["file_token"])
    elif tool == "drive.update":
        result = drive.update_file_meta(
            payload["file_token"],
            name=payload.get("name"),
            folder_token=payload.get("folder_token"),
        )
    elif tool == "drive.delete":
        result = drive.delete_node(
            payload["token"],
            recursive=bool(payload.get("recursive") or False),
            request_id=payload.get("request_id"),
            node_type=str(payload.get("node_type") or "file"),
        )
    elif tool == "drive.move":
        result = drive.move_node(payload["token"], payload["target_folder_token"], payload.get("request_id"))
    elif tool == "upload.bytes":
        result = upload.upload_bytes(
            payload["parent_token"],
            payload["name"],
            str(payload["content"]).encode("utf-8"),
            mime=str(payload.get("mime") or "application/octet-stream"),
        )
    elif tool == "docs.create":
        result = docs.create(payload["title"], payload.get("folder_token"))
    elif tool == "docs.read":
        result = docs.read(payload["doc_token"])
    elif tool == "docs.read_blocks":
        result = docs.list_blocks(payload["doc_token"])
    elif tool == "docs.append":
        result = docs.append_text(payload["doc_token"], payload["text"])
    elif tool == "docs.append_heading":
        result = docs.append_heading(
            payload["doc_token"],
            payload["text"],
            level=int(payload.get("level") or 1),
            index=payload.get("index"),
        )
    elif tool == "docs.append_bullet":
        result = docs.append_bullet(payload["doc_token"], payload["text"], index=payload.get("index"))
    elif tool == "docs.append_styled":
        result = docs.append_styled_text(
            payload["doc_token"],
            payload["text"],
            bold=bool(payload.get("bold") or False),
            italic=bool(payload.get("italic") or False),
            underline=bool(payload.get("underline") or False),
            index=payload.get("index"),
        )
    elif tool == "docs.update":
        result = docs.update_text(payload["doc_token"], payload["text"], block_id=payload.get("block_id"))
    elif tool == "docs.delete":
        result = docs.delete(payload["doc_token"])
    elif tool == "sheets.create":
        result = sheets.create(payload["title"], payload.get("folder_token"))
    elif tool == "sheets.read_range":
        result = sheets.read_range(payload["sheet_token"], payload["range"])
    elif tool == "sheets.write":
        result = sheets.write_range(payload["sheet_token"], payload["range"], payload["values"])
    elif tool == "sheets.append_rows":
        result = sheets.append_rows(payload["sheet_token"], payload["range"], payload["values"])
    elif tool == "sheets.delete_range":
        result = sheets.delete_range(payload["sheet_token"], payload["range"])
    elif tool == "slides.append":
        result = slides.append_slide(payload["slides_token"], payload["title"])
    elif tool == "bitable.list_tables":
        result = bitable.list_tables(payload["app_token"])
    elif tool == "bitable.list_fields":
        result = bitable.list_fields(payload["app_token"], payload["table_id"])
    elif tool == "bitable.create_table":
        result = bitable.create_table(payload["app_token"], payload["name"])
    elif tool == "bitable.read_records":
        result = bitable.read_records(payload["app_token"], payload["table_id"], view_id=payload.get("view_id"))
    elif tool == "bitable.create_record":
        result = bitable.create_record(payload["app_token"], payload["table_id"], payload["fields"])
    elif tool == "bitable.update_record":
        result = bitable.update_record(payload["app_token"], payload["table_id"], payload["record_id"], payload["fields"])
    elif tool == "bitable.delete_record":
        result = bitable.delete_record(payload["app_token"], payload["table_id"], payload["record_id"])
    else:
        _print({"ok": False, "error": f"unsupported tool: {tool}"})
        return 2

    _print({"ok": True, "tool": tool, "result": result})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
