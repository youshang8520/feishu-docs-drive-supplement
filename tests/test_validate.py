import json
import time
import urllib.error

import requests

from cc_feishu.auth.token_provider import FeishuTokenProvider
from cc_feishu.cli import DEFAULT_AUTH_SCOPE, main
from cc_feishu.config import (
    FeishuConfig,
    clear_pending_auth_state,
    load_config,
    load_pending_auth_state,
    save_pending_auth_state,
    validate_config,
)
from cc_feishu.errors import AuthError


def test_validate_requires_credentials_without_static_token(monkeypatch):
    monkeypatch.delenv("FEISHU_TENANT_ACCESS_TOKEN", raising=False)
    cfg = FeishuConfig(app_id="", app_secret="", base_url="https://open.feishu.cn", timeout_seconds=30)
    errs = validate_config(cfg)
    assert any("FEISHU_APP_ID" in e for e in errs)
    assert any("FEISHU_APP_SECRET" in e for e in errs)


def test_validate_allows_static_token_without_app_credentials():
    cfg = FeishuConfig(
        app_id="",
        app_secret="",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
        tenant_access_token="token",
    )
    errs = validate_config(cfg)
    assert errs == []


def test_load_config_inherits_from_cc_connect_toml(monkeypatch, tmp_path):
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

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.delenv("FEISHU_APP_ID", raising=False)
    monkeypatch.delenv("FEISHU_APP_SECRET", raising=False)
    monkeypatch.delenv("FEISHU_TENANT_ACCESS_TOKEN", raising=False)

    cfg = load_config()
    assert cfg.app_id == "inherit_app"
    assert cfg.app_secret == "inherit_secret"


def test_load_config_env_overrides_cc_connect_toml(monkeypatch, tmp_path):
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

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setenv("FEISHU_APP_ID", "env_app")
    monkeypatch.setenv("FEISHU_APP_SECRET", "env_secret")

    cfg = load_config()
    assert cfg.app_id == "env_app"
    assert cfg.app_secret == "env_secret"


def test_cli_invalid_json_fields_returns_nonzero(monkeypatch, capsys):
    monkeypatch.setenv("FEISHU_TENANT_ACCESS_TOKEN", "token")
    exit_code = main([
        "--dry-run",
        "bitable",
        "create-record",
        "--app",
        "app",
        "--table",
        "tbl",
        "--fields",
        "{bad_json}",
    ])
    out = capsys.readouterr().out
    assert exit_code != 0
    data = json.loads(out)
    assert data["ok"] is False


def test_cli_bitable_list_fields_prints_result(monkeypatch, tmp_path, capsys):
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

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))

    def _fake_list_fields(self, app_token, table_id):
        assert app_token == "app_tok"
        assert table_id == "tbl_tok"
        return {"items": [{"field_name": "文本", "ui_type": "Text"}]}

    monkeypatch.setattr("cc_feishu.cli.BitableService.list_fields", _fake_list_fields)

    exit_code = main(["bitable", "list-fields", "--app", "app_tok", "--table", "tbl_tok"])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["items"][0]["field_name"] == "文本"


def test_cli_auth_status_reports_auto_user_effective_mode(monkeypatch, tmp_path, capsys):
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
                "auth_mode": "auto",
                "user_access_token": "uat",
                "user_refresh_token": "urt",
                "user_token_expires_at": int(time.time()) + 7200,
                "user_refresh_expires_at": int(time.time()) + 86400,
                "user_open_id": "ou_user",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.USER_AUTH_FILE", user_auth)
    monkeypatch.setattr("cc_feishu.cli.USER_AUTH_FILE", user_auth)

    exit_code = main(["auth", "status"])
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["auth_mode"] == "auto"
    assert data["effective_auth"] == "user"
    assert data["has_user_refresh_token"] is True
    assert data["user_auth_file"] == str(user_auth)


def test_cli_auth_import_writes_sidecar(monkeypatch, tmp_path, capsys):
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

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.USER_AUTH_FILE", user_auth)
    monkeypatch.setattr("cc_feishu.cli.USER_AUTH_FILE", user_auth)

    exit_code = main(
        [
            "auth",
            "import",
            "--refresh-token",
            "refresh_token",
            "--access-token",
            "access_token",
            "--expires-at",
            "123",
            "--refresh-expires-at",
            "456",
            "--open-id",
            "ou_123",
            "--mode",
            "user",
        ]
    )
    out = capsys.readouterr().out

    assert exit_code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["auth_mode"] == "user"
    assert data["has_user_refresh_token"] is True
    assert data["has_user_access_token"] is True

    persisted = json.loads(user_auth.read_text(encoding="utf-8"))
    assert persisted == {
        "auth_mode": "user",
        "user_access_token": "access_token",
        "user_refresh_token": "refresh_token",
        "user_token_expires_at": 123,
        "user_refresh_expires_at": 456,
        "user_open_id": "ou_123",
    }


def test_cli_auth_login_prints_link_and_persists_user_auth(monkeypatch, tmp_path, capsys):
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

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.USER_AUTH_FILE", user_auth)
    monkeypatch.setattr("cc_feishu.cli.USER_AUTH_FILE", user_auth)

    start_calls: list[str] = []

    def _fake_start(self, scope):
        start_calls.append(scope)
        return {
            "device_code": "device_code",
            "user_code": "user_code",
            "verification_uri": "https://accounts.feishu.cn/verify",
            "verification_uri_complete": "https://accounts.feishu.cn/verify?user_code=user_code",
            "interval": 2,
            "expires_in": 900,
            "scope": scope,
        }

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
        persisted = json.loads(user_auth.read_text(encoding="utf-8"))
        return {
            "ok": True,
            "auth_mode": persisted["auth_mode"],
            "user_open_id": persisted["user_open_id"],
            "has_user_access_token": bool(persisted["user_access_token"]),
            "has_user_refresh_token": bool(persisted["user_refresh_token"]),
            "user_token_expires_at": persisted["user_token_expires_at"],
            "user_refresh_expires_at": persisted["user_refresh_expires_at"],
            "user_info": {"open_id": persisted["user_open_id"], "name": "Claude User"},
        }

    monkeypatch.setattr(FeishuTokenProvider, "start_device_authorization", _fake_start)
    monkeypatch.setattr(FeishuTokenProvider, "poll_device_authorization", _fake_poll)

    exit_code = main(["auth", "login", "--timeout", "30"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert start_calls == [DEFAULT_AUTH_SCOPE]
    assert '"status": "pending_authorization"' in out
    assert '"verification_uri_complete": "https://accounts.feishu.cn/verify?user_code=user_code"' in out
    assert '"status": "authorized"' in out
    persisted = json.loads(user_auth.read_text(encoding="utf-8"))
    assert persisted["auth_mode"] == "user"
    assert persisted["user_open_id"] == "ou_login"


def test_device_authorization_adds_offline_access(monkeypatch):
    cfg = FeishuConfig(
        app_id="app",
        app_secret="secret",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
    )
    provider = FeishuTokenProvider(cfg)
    captured = {}

    def _fake_post_form_json(url, form, headers=None):
        captured["url"] = url
        captured["form"] = form
        captured["headers"] = headers
        return {"code": 0, "device_code": "dev"}

    monkeypatch.setattr(provider, "_post_form_json", _fake_post_form_json)

    provider.start_device_authorization("docs:document:read docs:document:write")
    assert captured["url"] == "https://accounts.feishu.cn/oauth/v1/device_authorization"
    assert captured["form"]["client_id"] == "app"
    assert "offline_access" in captured["form"]["scope"]
    assert captured["headers"]["Authorization"].startswith("Basic ")


def test_token_provider_retries_transient_ssl_errors(monkeypatch):

    cfg = FeishuConfig(
        app_id="app",
        app_secret="secret",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
    )
    provider = FeishuTokenProvider(cfg)

    calls = {"count": 0}

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"code": 0, "tenant_access_token": "fresh_token", "expire": 7200}).encode("utf-8")

    def _fake_urlopen(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise urllib.error.URLError("[SSL: UNEXPECTED_EOF_WHILE_READING]")
        return _Resp()

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("cc_feishu.auth.token_provider.time.sleep", lambda *_args, **_kwargs: None)

    token = provider.get_tenant_token()
    assert token == "fresh_token"
    assert calls["count"] == 3


def test_token_provider_raises_after_non_transient_error(monkeypatch):
    cfg = FeishuConfig(
        app_id="app",
        app_secret="secret",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
    )
    provider = FeishuTokenProvider(cfg)

    def _fake_urlopen(*args, **kwargs):
        raise urllib.error.URLError("bad url")

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    try:
        provider.get_tenant_token()
        assert False, "expected AuthError"
    except AuthError as exc:
        assert "Failed to get tenant token" in str(exc)



def test_validate_user_mode_requires_refresh_token():
    cfg = FeishuConfig(
        app_id="app",
        app_secret="secret",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
        auth_mode="user",
        user_refresh_token="",
    )
    errs = validate_config(cfg)
    assert any("FEISHU_USER_REFRESH_TOKEN" in e for e in errs)


def test_load_config_reads_user_auth_sidecar(monkeypatch, tmp_path):
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
                "user_token_expires_at": 123,
                "user_refresh_expires_at": 456,
                "user_open_id": "ou_user",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setattr("cc_feishu.config.USER_AUTH_FILE", user_auth)

    cfg = load_config()
    assert cfg.auth_mode == "user"
    assert cfg.user_refresh_token == "urt"
    assert cfg.user_open_id == "ou_user"


def test_user_mode_env_overrides_sidecar(monkeypatch, tmp_path):
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
    user_auth.write_text(json.dumps({"auth_mode": "tenant", "user_refresh_token": "sidecar_urt"}), encoding="utf-8")

    monkeypatch.setenv("CC_CONNECT_CONFIG_PATH", str(cfg_file))
    monkeypatch.setenv("FEISHU_AUTH_MODE", "user")
    monkeypatch.setenv("FEISHU_USER_REFRESH_TOKEN", "env_urt")
    monkeypatch.setattr("cc_feishu.config.USER_AUTH_FILE", user_auth)

    cfg = load_config()
    assert cfg.auth_mode == "user"
    assert cfg.user_refresh_token == "env_urt"


def test_token_provider_refreshes_user_token(monkeypatch):
    cfg = FeishuConfig(
        app_id="app",
        app_secret="secret",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
        auth_mode="user",
        user_refresh_token="refresh_token",
    )
    provider = FeishuTokenProvider(cfg)

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "code": 0,
                    "access_token": "user_access",
                    "refresh_token": "next_refresh",
                    "expires_in": 7200,
                    "refresh_token_expires_in": 604800,
                }
            ).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: _Resp())
    monkeypatch.setattr("cc_feishu.auth.token_provider.save_user_auth_state", lambda *_args, **_kwargs: None)

    token = provider.get_user_token()
    assert token == "user_access"




def test_pending_auth_state_roundtrip(monkeypatch, tmp_path):
    pending_auth = tmp_path / "feishu_pending_auth.json"
    monkeypatch.setattr("cc_feishu.config.PENDING_AUTH_FILE", pending_auth)

    save_pending_auth_state(
        {
            "device_code": "device_code",
            "verification_uri_complete": "https://accounts.feishu.cn/verify?user_code=user_code",
            "expires_at": 4102444800,
        }
    )

    loaded = load_pending_auth_state()
    assert loaded["device_code"] == "device_code"
    assert loaded["verification_uri_complete"] == "https://accounts.feishu.cn/verify?user_code=user_code"

    clear_pending_auth_state()
    assert load_pending_auth_state() == {}


def test_token_provider_user_refresh_raises_on_error(monkeypatch):
    cfg = FeishuConfig(
        app_id="app",
        app_secret="secret",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
        auth_mode="user",
        user_refresh_token="refresh_token",
    )
    provider = FeishuTokenProvider(cfg)

    class _ErrResp:
        def read(self):
            return b'{"code":99991663,"msg":"bad refresh"}'

        def close(self):
            return None

    def _raise(*args, **kwargs):
        raise __import__("urllib.error").error.HTTPError("u", 400, "bad", None, _ErrResp())

    monkeypatch.setattr("urllib.request.urlopen", _raise)

    try:
        provider.get_user_token()
        assert False, "expected AuthError"
    except AuthError as exc:
        assert "bad refresh" in str(exc)


