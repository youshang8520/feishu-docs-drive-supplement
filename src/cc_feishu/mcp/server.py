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


def _auth_start(provider: FeishuTokenProvider, payload: dict[str, Any]) -> dict[str, Any]:
    scope = payload.get("scope") or DEFAULT_AUTH_SCOPE
    mode = payload.get("mode") or "user"
    force = payload.get("force", False)

    pending = load_pending_auth_state()
    now = int(time.time())
    pending_active = bool(pending.get("device_code")) and now < int(pending.get("expires_at", 0) or 0)

    if pending_active and not force:
        link = pending.get("verification_uri_complete") or pending.get("verification_uri")
        return {
            "ok": True,
            "status": "pending_authorization",
            "message": "Reusing existing pending authorization.",
            "verification_uri_complete": link,
            "device_code": pending.get("device_code"),
            "expires_in": max(0, int(pending.get("expires_at", 0)) - now),
        }

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

    return {
        "ok": True,
        "status": "pending_authorization",
        "message": "Authorization started. Please visit the verification URL.",
        "verification_uri_complete": pending["verification_uri_complete"],
        "device_code": pending["device_code"],
        "expires_in": pending["expires_in"],
    }


def _auth_poll(provider: FeishuTokenProvider, payload: dict[str, Any]) -> dict[str, Any]:
            _print(result)
            return

        if args.tool == "auth.import":
            # Import existing tokens
            user_access_token = payload.get("user_access_token", "")
            user_refresh_token = payload.get("user_refresh_token", "")
            user_token_expires_at = payload.get("user_token_expires_at", 0)
            user_refresh_expires_at = payload.get("user_refresh_expires_at", 0)
            user_open_id = payload.get("user_open_id", "")

            save_user_auth_state({
                "user_access_token": user_access_token,
                "user_refresh_token": user_refresh_token,
                "user_token_expires_at": user_token_expires_at,
                "user_refresh_expires_at": user_refresh_expires_at,
                "user_open_id": user_open_id,
            })

            _print({"ok": True, "message": "User auth imported successfully"})
            return

        # Validate config for resource operations
        errors = validate_config(config)
        if errors:
            _print({"ok": False, "errors": errors})
            return

        client = init_provider(config)

        # Drive operations
        if args.tool == "drive.list":
            drive = DriveService(client)
            result = drive.list_folder(
                payload.get("folder_token", "root"),
                payload.get("page_token")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "drive.create_folder":
            drive = DriveService(client)
            result = drive.create_folder(
                payload["parent_token"],
                payload["name"],
                payload.get("request_id")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "drive.read":
            drive = DriveService(client)
            result = drive.read_file_meta(payload["file_token"])
            _print({"ok": True, "result": result})
            return

        if args.tool == "drive.update":
            drive = DriveService(client)
            result = drive.update_file_meta(
                payload["file_token"],
                name=payload.get("name"),
                folder_token=payload.get("folder_token")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "drive.move":
            drive = DriveService(client)
            result = drive.move_node(
                payload["file_token"],
                payload["target_folder_token"],
                payload.get("request_id")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "drive.delete":
            drive = DriveService(client)
            result = drive.delete_node(
                payload["file_token"],
                recursive=payload.get("recursive", False),
                request_id=payload.get("request_id")
            )
            _print({"ok": True, "result": result})
            return

        # Upload operations
        if args.tool == "upload.bytes":
            upload = UploadService(client)
            content = payload["content"]
            if isinstance(content, str):
                content = content.encode("utf-8")
            result = upload.upload_bytes(
                payload["parent_token"],
                payload["name"],
                content,
                mime=payload.get("mime")
            )
            _print({"ok": True, "result": result})
            return

        # Docs operations
        if args.tool == "docs.create":
            docs = DocsService(client)
            result = docs.create(
                payload["title"],
                folder_token=payload.get("folder_token")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "docs.read":
            docs = DocsService(client)
            result = docs.read(payload["doc_token"])
            _print({"ok": True, "result": result})
            return

        if args.tool == "docs.read_blocks":
            docs = DocsService(client)
            result = docs.list_blocks(payload["doc_token"])
            _print({"ok": True, "result": result})
            return

        if args.tool == "docs.append":
            docs = DocsService(client)
            result = docs.append_text(
                payload["doc_token"],
                payload["text"]
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "docs.append_heading":
            docs = DocsService(client)
            result = docs.append_heading(
                payload["doc_token"],
                payload["text"],
                level=payload.get("level", 1),
                index=payload.get("index")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "docs.append_bullet":
            docs = DocsService(client)
            result = docs.append_bullet(
                payload["doc_token"],
                payload["text"],
                index=payload.get("index")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "docs.append_styled":
            docs = DocsService(client)
            result = docs.append_styled_text(
                payload["doc_token"],
                payload["text"],
                bold=payload.get("bold", False),
                italic=payload.get("italic", False),
                underline=payload.get("underline", False),
                index=payload.get("index")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "docs.update":
            docs = DocsService(client)
            result = docs.update_text(
                payload["doc_token"],
                payload["text"],
                block_id=payload.get("block_id")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "docs.delete":
            docs = DocsService(client)
            result = docs.delete(payload["doc_token"])
            _print({"ok": True, "result": result})
            return

        # Sheets operations
        if args.tool == "sheets.create":
            sheets = SheetsService(client)
            result = sheets.create(
                payload["title"],
                folder_token=payload.get("folder_token")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "sheets.read_range":
            sheets = SheetsService(client)
            result = sheets.read_range(
                payload["sheet_token"],
                payload["range"]
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "sheets.write":
            sheets = SheetsService(client)
            result = sheets.write_range(
                payload["sheet_token"],
                payload["range"],
                payload["values"]
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "sheets.append_rows":
            sheets = SheetsService(client)
            result = sheets.append_rows(
                payload["sheet_token"],
                payload["range"],
                payload["values"]
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "sheets.delete_range":
            sheets = SheetsService(client)
            result = sheets.delete_range(
                payload["sheet_token"],
                payload["range"]
            )
            _print({"ok": True, "result": result})
            return

        # Bitable operations
        if args.tool == "bitable.list_tables":
            bitable = BitableService(client)
            result = bitable.list_tables(payload["app_token"])
            _print({"ok": True, "result": result})
            return

        if args.tool == "bitable.list_fields":
            bitable = BitableService(client)
            result = bitable.list_fields(
                payload["app_token"],
                payload["table_id"]
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "bitable.create_table":
            bitable = BitableService(client)
            result = bitable.create_table(
                payload["app_token"],
                payload["name"]
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "bitable.read_records":
            bitable = BitableService(client)
            result = bitable.read_records(
                payload["app_token"],
                payload["table_id"],
                page_token=payload.get("page_token")
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "bitable.create_record":
            bitable = BitableService(client)
            result = bitable.create_record(
                payload["app_token"],
                payload["table_id"],
                payload["fields"]
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "bitable.update_record":
            bitable = BitableService(client)
            result = bitable.update_record(
                payload["app_token"],
                payload["table_id"],
                payload["record_id"],
                payload["fields"]
            )
            _print({"ok": True, "result": result})
            return

        if args.tool == "bitable.delete_record":
            bitable = BitableService(client)
            result = bitable.delete_record(
                payload["app_token"],
                payload["table_id"],
                payload["record_id"]
            )
            _print({"ok": True, "result": result})
            return

        _print({"ok": False, "error": f"Unknown tool: {args.tool}"})

    except Exception as e:
        _print({"ok": False, "error": str(e)})


if __name__ == "__main__":
    main()
