import json

from cc_feishu.chat_router import route_command


def test_route_auth_command_returns_authorization_link(monkeypatch, tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
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
    pending_auth = tmp_path / "feishu_pending_auth.json"
    user_auth = tmp_path / "feishu_user_auth.json"

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.PENDING_AUTH_FILE", pending_auth)
    monkeypatch.setattr("cc_feishu.chat_router.PENDING_AUTH_FILE", pending_auth)
    monkeypatch.setattr("cc_feishu.config.USER_AUTH_FILE", user_auth)
    monkeypatch.setattr("cc_feishu.chat_router.USER_AUTH_FILE", user_auth)

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

    monkeypatch.setattr("cc_feishu.chat_router.FeishuTokenProvider.start_device_authorization", _fake_start)

    data = route_command("/feishu auth")

    assert data["ok"] is True
    assert data["tool"] == "auth.start"
    assert data["status"] == "pending_authorization"
    assert "verification_uri_complete" in data
    assert pending_auth.exists() is True


def test_route_docs_update_block_command(monkeypatch, tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
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
    user_auth = tmp_path / "feishu_user_auth.json"
    user_auth.write_text(
        json.dumps(
            {
                "auth_mode": "user",
                "user_access_token": "uat",
                "user_refresh_token": "urt",
                "user_token_expires_at": 4102444800,
                "user_refresh_expires_at": 4102444800,
                "user_open_id": "ou_user",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.USER_AUTH_FILE", user_auth)
    monkeypatch.setattr("cc_feishu.chat_router.USER_AUTH_FILE", user_auth)

    def _fake_update(self, doc_token, text, block_id=None):
        assert doc_token == "doc_tok"
        assert text == "updated text"
        assert block_id == "blk_tok"
        return {"doc_token": doc_token, "block_id": block_id, "text": text}

    monkeypatch.setattr("cc_feishu.chat_router.DocsService.update_text", _fake_update)

    data = route_command('/feishu docs update --doc doc_tok --block blk_tok --text "updated text"')

    assert data["ok"] is True
    assert data["tool"] == "docs.update"
    assert data["result"]["block_id"] == "blk_tok"


def test_route_bitable_list_fields_command(monkeypatch, tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
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
    user_auth = tmp_path / "feishu_user_auth.json"
    user_auth.write_text(
        json.dumps(
            {
                "auth_mode": "user",
                "user_access_token": "uat",
                "user_refresh_token": "urt",
                "user_token_expires_at": 4102444800,
                "user_refresh_expires_at": 4102444800,
                "user_open_id": "ou_user",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.USER_AUTH_FILE", user_auth)
    monkeypatch.setattr("cc_feishu.chat_router.USER_AUTH_FILE", user_auth)

    def _fake_list_fields(self, app_token, table_id):
        assert app_token == "app_tok"
        assert table_id == "tbl_tok"
        return {"items": [{"field_name": "文本"}]}

    monkeypatch.setattr("cc_feishu.chat_router.BitableService.list_fields", _fake_list_fields)

    data = route_command('/feishu bitable list-fields --app app_tok --table tbl_tok')

    assert data["ok"] is True
    assert data["tool"] == "bitable.list_fields"
    assert data["result"]["items"][0]["field_name"] == "文本"
