import json

from cc_feishu.mcp.server import main


def _write_cfg(path):
    path.write_text(
        """
[[projects]]
name = "claudecode"

[[projects.platforms]]
type = "feishu"
[projects.platforms.options]
app_id = "inherit_app"
app_secret = "inherit_secret"
""".strip(),
        encoding="utf-8",
    )


def test_mcp_auth_status_returns_ok(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    exit_code = main(["auth.status", "--payload", "{}"])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["has_app_credentials"] is True
    assert data["has_pending_auth"] is False


def test_mcp_auth_start_returns_verification_link(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    pending_auth = tmp_path / "feishu_pending_auth.json"

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.PENDING_AUTH_FILE", pending_auth)
    monkeypatch.setattr("cc_feishu.mcp.server.PENDING_AUTH_FILE", pending_auth)

    def _fake_start(self, scope):
        return {
            "device_code": "device_code",
            "user_code": "user_code",
            "verification_uri": "https://accounts.feishu.cn/verify",
            "verification_uri_complete": "https://accounts.feishu.cn/verify?user_code=user_code",
            "interval": 2,
            "expires_in": 900,
            "scope": scope,
        }

    monkeypatch.setattr("cc_feishu.mcp.server.FeishuTokenProvider.start_device_authorization", _fake_start)

    exit_code = main(["auth.start", "--payload", "{}"])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["status"] == "pending_authorization"
    assert data["verification_uri_complete"] == "https://accounts.feishu.cn/verify?user_code=user_code"
    assert data["device_code"] == "device_code"
    persisted = json.loads(pending_auth.read_text(encoding="utf-8"))
    assert persisted["device_code"] == "device_code"
    assert persisted["verification_uri_complete"] == "https://accounts.feishu.cn/verify?user_code=user_code"


def test_mcp_auth_start_reuses_pending_link(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    pending_auth = tmp_path / "feishu_pending_auth.json"
    pending_auth.write_text(
        json.dumps(
            {
                "auth_mode": "user",
                "scope": "offline_access drive:drive",
                "verification_uri": "https://accounts.feishu.cn/verify",
                "verification_uri_complete": "https://accounts.feishu.cn/verify?user_code=user_code",
                "user_code": "user_code",
                "device_code": "device_code",
                "interval": 2,
                "expires_in": 900,
                "expires_at": 4102444800,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.PENDING_AUTH_FILE", pending_auth)
    monkeypatch.setattr("cc_feishu.mcp.server.PENDING_AUTH_FILE", pending_auth)

    def _unexpected_start(self, scope):
        raise AssertionError("auth.start should reuse the pending authorization")

    monkeypatch.setattr("cc_feishu.mcp.server.FeishuTokenProvider.start_device_authorization", _unexpected_start)

    exit_code = main(["auth.start", "--payload", "{}"])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["status"] == "pending_authorization"
    assert data["device_code"] == "device_code"
    assert data["verification_uri_complete"] == "https://accounts.feishu.cn/verify?user_code=user_code"


def test_mcp_auth_send_link_sends_chat_message(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    pending_auth = tmp_path / "feishu_pending_auth.json"

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.PENDING_AUTH_FILE", pending_auth)
    monkeypatch.setattr("cc_feishu.mcp.server.PENDING_AUTH_FILE", pending_auth)

    def _fake_start(self, scope):
        return {
            "device_code": "device_code",
            "user_code": "user_code",
            "verification_uri": "https://accounts.feishu.cn/verify",
            "verification_uri_complete": "https://accounts.feishu.cn/verify?user_code=user_code",
            "interval": 2,
            "expires_in": 900,
            "scope": scope,
        }

    def _fake_send_text(self, receive_id, text, *, receive_id_type="chat_id"):
        assert receive_id == "oc_test_chat"
        assert receive_id_type == "chat_id"
        assert text == "请点击链接完成飞书授权：https://accounts.feishu.cn/verify?user_code=user_code"
        return {"message_id": "om_message"}

    monkeypatch.setattr("cc_feishu.mcp.server.FeishuTokenProvider.start_device_authorization", _fake_start)
    monkeypatch.setattr("cc_feishu.mcp.server.MessagesService.send_text", _fake_send_text)

    payload = json.dumps({"receive_id": "oc_test_chat"})
    exit_code = main(["auth.send_link", "--payload", payload])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["status"] == "pending_authorization"
    assert data["message"] == "Sent Feishu authorization link."
    assert data["receive_id"] == "oc_test_chat"
    assert data["receive_id_type"] == "chat_id"
    assert data["sent_message"]["message_id"] == "om_message"
    persisted = json.loads(pending_auth.read_text(encoding="utf-8"))
    assert persisted["device_code"] == "device_code"


def test_mcp_auth_poll_uses_pending_state_when_device_code_is_omitted(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    pending_auth = tmp_path / "feishu_pending_auth.json"
    pending_auth.write_text(
        json.dumps(
            {
                "auth_mode": "user",
                "scope": "offline_access drive:drive",
                "verification_uri": "https://accounts.feishu.cn/verify",
                "verification_uri_complete": "https://accounts.feishu.cn/verify?user_code=user_code",
                "user_code": "user_code",
                "device_code": "device_code",
                "interval": 2,
                "expires_in": 900,
                "expires_at": 4102444800,
            }
        ),
        encoding="utf-8",
    )
    user_auth = tmp_path / "feishu_user_auth.json"

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.PENDING_AUTH_FILE", pending_auth)
    monkeypatch.setattr("cc_feishu.mcp.server.PENDING_AUTH_FILE", pending_auth)
    monkeypatch.setattr("cc_feishu.config.USER_AUTH_FILE", user_auth)
    monkeypatch.setattr("cc_feishu.mcp.server.USER_AUTH_FILE", user_auth)

    def _fake_poll(self, device_code, *, interval_seconds, timeout_seconds, auth_mode):
        assert device_code == "device_code"
        assert interval_seconds == 2
        assert timeout_seconds == 30
        assert auth_mode == "user"
        user_auth.write_text(
            json.dumps(
                {
                    "auth_mode": auth_mode,
                    "user_access_token": "access_token",
                    "user_refresh_token": "refresh_token",
                    "user_token_expires_at": 1234,
                    "user_refresh_expires_at": 5678,
                    "user_open_id": "ou_login",
                }
            ),
            encoding="utf-8",
        )
        return {
            "ok": True,
            "auth_mode": auth_mode,
            "user_open_id": "ou_login",
            "has_user_access_token": True,
            "has_user_refresh_token": True,
            "user_token_expires_at": 1234,
            "user_refresh_expires_at": 5678,
            "user_info": {"open_id": "ou_login", "name": "Claude User"},
        }

    monkeypatch.setattr("cc_feishu.mcp.server.FeishuTokenProvider.poll_device_authorization", _fake_poll)

    payload = json.dumps({"timeout": 30})
    exit_code = main(["auth.poll", "--payload", payload])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["status"] == "authorized"
    persisted = json.loads(user_auth.read_text(encoding="utf-8"))
    assert persisted["auth_mode"] == "user"
    assert persisted["user_open_id"] == "ou_login"
    assert pending_auth.exists() is False


def test_mcp_auth_status_reports_pending_auth(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    pending_auth = tmp_path / "feishu_pending_auth.json"
    pending_auth.write_text(
        json.dumps(
            {
                "auth_mode": "user",
                "scope": "offline_access drive:drive",
                "verification_uri": "https://accounts.feishu.cn/verify",
                "verification_uri_complete": "https://accounts.feishu.cn/verify?user_code=user_code",
                "user_code": "user_code",
                "device_code": "device_code",
                "interval": 2,
                "expires_in": 900,
                "expires_at": 4102444800,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.PENDING_AUTH_FILE", pending_auth)
    monkeypatch.setattr("cc_feishu.mcp.server.PENDING_AUTH_FILE", pending_auth)

    exit_code = main(["auth.status", "--payload", "{}"])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["has_pending_auth"] is True
    assert data["pending_auth"]["device_code"] == "device_code"


def test_mcp_bitable_list_fields_routes_to_service(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    def _fake_list_fields(self, app_token, table_id):
        assert app_token == "app_tok"
        assert table_id == "tbl_tok"
        return {"items": [{"field_name": "文本", "ui_type": "Text"}]}

    monkeypatch.setattr("cc_feishu.mcp.server.BitableService.list_fields", _fake_list_fields)

    payload = json.dumps({"app_token": "app_tok", "table_id": "tbl_tok"})
    exit_code = main(["bitable.list_fields", "--payload", payload])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "bitable.list_fields"
    assert data["result"]["items"][0]["field_name"] == "文本"


def test_mcp_drive_update_routes_to_service(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    def _fake_update(self, file_token, *, name=None, folder_token=None):
        assert file_token == "file_tok"
        assert name == "new_name"
        assert folder_token == "folder_tok"
        return {"ok": True, "file_token": file_token, "name": name, "folder_token": folder_token}

    monkeypatch.setattr("cc_feishu.mcp.server.DriveService.update_file_meta", _fake_update)

    payload = json.dumps({"file_token": "file_tok", "name": "new_name", "folder_token": "folder_tok"})
    exit_code = main(["drive.update", "--payload", payload])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["tool"] == "drive.update"
    assert data["result"]["file_token"] == "file_tok"


def test_mcp_docs_update_routes_to_service(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    def _fake_update(self, doc_token, text, block_id=None):
        assert doc_token == "doc_tok"
        assert text == "updated text"
        assert block_id == "blk_tok"
        return {"ok": True, "doc_token": doc_token, "text": text, "block_id": block_id}

    monkeypatch.setattr("cc_feishu.mcp.server.DocsService.update_text", _fake_update)

    payload = json.dumps({"doc_token": "doc_tok", "text": "updated text", "block_id": "blk_tok"})
    exit_code = main(["docs.update", "--payload", payload])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "docs.update"
    assert data["result"]["doc_token"] == "doc_tok"
    assert data["result"]["block_id"] == "blk_tok"


def test_mcp_docs_read_blocks_routes_to_service(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    def _fake_list_blocks(self, doc_token):
        assert doc_token == "doc_tok"
        return {"items": [{"block_id": "blk_tok"}]}

    monkeypatch.setattr("cc_feishu.mcp.server.DocsService.list_blocks", _fake_list_blocks)

    payload = json.dumps({"doc_token": "doc_tok"})
    exit_code = main(["docs.read_blocks", "--payload", payload])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "docs.read_blocks"
    assert data["result"]["items"][0]["block_id"] == "blk_tok"


def test_mcp_bitable_update_and_delete_route_to_service(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    def _fake_update(self, app_token, table_id, record_id, fields):
        assert app_token == "app_tok"
        assert table_id == "tbl_tok"
        assert record_id == "rec_tok"
        assert fields == {"文本": "更新"}
        return {"action": "update", "record_id": record_id}

    def _fake_delete(self, app_token, table_id, record_id):
        assert app_token == "app_tok"
        assert table_id == "tbl_tok"
        assert record_id == "rec_tok"
        return {"action": "delete", "record_id": record_id}

    monkeypatch.setattr("cc_feishu.mcp.server.BitableService.update_record", _fake_update)
    monkeypatch.setattr("cc_feishu.mcp.server.BitableService.delete_record", _fake_delete)

    update_payload = json.dumps({"app_token": "app_tok", "table_id": "tbl_tok", "record_id": "rec_tok", "fields": {"文本": "更新"}})
    exit_code = main(["bitable.update_record", "--payload", update_payload])
    out = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "bitable.update_record"
    assert data["result"]["action"] == "update"

    delete_payload = json.dumps({"app_token": "app_tok", "table_id": "tbl_tok", "record_id": "rec_tok"})
    exit_code = main(["bitable.delete_record", "--payload", delete_payload])
    out = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "bitable.delete_record"
    assert data["result"]["action"] == "delete"


def test_mcp_upload_bytes_routes_to_service(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    def _fake_upload(self, parent_token, file_name, content, mime="application/octet-stream"):
        assert parent_token == "folder_tok"
        assert file_name == "note.md"
        assert content == b"hello"
        assert mime == "text/markdown"
        return {"file_token": "file_tok"}

    monkeypatch.setattr("cc_feishu.mcp.server.UploadService.upload_bytes", _fake_upload)

    payload = json.dumps({"parent_token": "folder_tok", "name": "note.md", "content": "hello", "mime": "text/markdown"})
    exit_code = main(["upload.bytes", "--payload", payload])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "upload.bytes"
    assert data["result"]["file_token"] == "file_tok"


def test_mcp_sheets_create_and_read_route_to_service(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    def _fake_create(self, title, folder_token=None):
        assert title == "sheet title"
        assert folder_token == "folder_tok"
        return {"spreadsheet_token": "sheet_tok"}

    def _fake_read(self, sheet_token, a1_range):
        assert sheet_token == "sheet_tok"
        assert a1_range == "A1:B2"
        return {"values": [["a", "b"]]}

    monkeypatch.setattr("cc_feishu.mcp.server.SheetsService.create", _fake_create)
    monkeypatch.setattr("cc_feishu.mcp.server.SheetsService.read_range", _fake_read)

    create_payload = json.dumps({"title": "sheet title", "folder_token": "folder_tok"})
    exit_code = main(["sheets.create", "--payload", create_payload])
    out = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "sheets.create"
    assert data["result"]["spreadsheet_token"] == "sheet_tok"

    read_payload = json.dumps({"sheet_token": "sheet_tok", "range": "A1:B2"})
    exit_code = main(["sheets.read_range", "--payload", read_payload])
    out = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "sheets.read_range"
    assert data["result"]["values"] == [["a", "b"]]


def test_mcp_drive_move_and_delete_route_to_service(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "config.toml"
    _write_cfg(cfg_file)
    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    def _fake_move(self, token, target_folder_token, request_id=None):
        assert token == "file_tok"
        assert target_folder_token == "folder_tok"
        assert request_id == "req_1"
        return {"action": "move", "token": token}

    def _fake_delete(self, token, recursive=False, request_id=None, node_type="file"):
        assert token == "file_tok"
        assert recursive is True
        assert request_id == "req_2"
        assert node_type == "file"
        return {"action": "delete", "token": token}

    monkeypatch.setattr("cc_feishu.mcp.server.DriveService.move_node", _fake_move)
    monkeypatch.setattr("cc_feishu.mcp.server.DriveService.delete_node", _fake_delete)

    move_payload = json.dumps({"token": "file_tok", "target_folder_token": "folder_tok", "request_id": "req_1"})
    exit_code = main(["drive.move", "--payload", move_payload])
    out = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "drive.move"
    assert data["result"]["action"] == "move"

    delete_payload = json.dumps({"token": "file_tok", "recursive": True, "request_id": "req_2", "node_type": "file"})
    exit_code = main(["drive.delete", "--payload", delete_payload])
    out = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(out)
    assert data["tool"] == "drive.delete"
    assert data["result"]["action"] == "delete"
