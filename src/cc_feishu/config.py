import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass(frozen=True)
class FeishuConfig:
    app_id: str
    app_secret: str
    base_url: str = "https://open.feishu.cn"
    timeout_seconds: int = 30
    dry_run: bool = False
    tenant_access_token: str = ""
    auth_mode: str = "auto"
    user_access_token: str = ""
    user_refresh_token: str = ""
    user_token_expires_at: int = 0
    user_refresh_expires_at: int = 0
    user_open_id: str = ""

    @property
    def has_static_token(self) -> bool:
        return bool(self.tenant_access_token.strip())

    @property
    def uses_user_auth(self) -> bool:
        return self.auth_mode.strip().lower() == "user"

    @property
    def prefers_user_auth(self) -> bool:
        return self.auth_mode.strip().lower() in {"auto", "user"}

    @property
    def has_user_refresh_token(self) -> bool:
        return bool(self.user_refresh_token.strip())


USER_AUTH_FILE = Path.home() / ".cc-connect" / "feishu_user_auth.json"
PENDING_AUTH_FILE = Path.home() / ".cc-connect" / "feishu_pending_auth.json"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int = 0) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _cc_connect_config_path() -> Path:
    explicit_path = os.getenv("CC_CONNECT_CONFIG_PATH", "").strip()
    if explicit_path:
        return Path(explicit_path)
    return Path.home() / ".cc-connect" / "config.toml"


def _load_cc_connect_feishu_options() -> dict[str, str]:
    config_path = _cc_connect_config_path()
    if not config_path.exists():
        return {}

    try:
        with config_path.open("rb") as f:
            raw: dict[str, Any] = tomllib.load(f)
    except Exception:
        return {}

    projects = raw.get("projects")
    if not isinstance(projects, list):
        return {}

    for project in projects:
        if not isinstance(project, dict):
            continue
        if str(project.get("name", "")).strip() != "claudecode":
            continue

        platforms = project.get("platforms")
        if not isinstance(platforms, list):
            continue

        for platform in platforms:
            if not isinstance(platform, dict):
                continue
            if str(platform.get("type", "")).strip() != "feishu":
                continue

            options = platform.get("options")
            if not isinstance(options, dict):
                return {}

            result: dict[str, str] = {}
            for key in ("app_id", "app_secret", "tenant_access_token", "base_url"):
                value = options.get(key)
                if isinstance(value, str) and value.strip():
                    result[key] = value.strip()

            token = options.get("token")
            if "tenant_access_token" not in result and isinstance(token, str) and token.strip():
                result["tenant_access_token"] = token.strip()

            return result

    return {}


def _load_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_user_auth_state() -> dict[str, Any]:
    return _load_json_file(USER_AUTH_FILE)


def load_pending_auth_state() -> dict[str, Any]:
    return _load_json_file(PENDING_AUTH_FILE)


def save_user_auth_state(config: FeishuConfig) -> None:
    _write_json_file(
        USER_AUTH_FILE,
        {
            "auth_mode": config.auth_mode,
            "user_access_token": config.user_access_token,
            "user_refresh_token": config.user_refresh_token,
            "user_token_expires_at": config.user_token_expires_at,
            "user_refresh_expires_at": config.user_refresh_expires_at,
            "user_open_id": config.user_open_id,
        },
    )


def save_pending_auth_state(state: dict[str, Any]) -> None:
    _write_json_file(PENDING_AUTH_FILE, state)


def clear_pending_auth_state() -> None:
    try:
        PENDING_AUTH_FILE.unlink()
    except FileNotFoundError:
        return


def load_config() -> FeishuConfig:
    timeout_raw = os.getenv("FEISHU_TIMEOUT_SECONDS", "30").strip() or "30"
    timeout = int(timeout_raw)
    if timeout <= 0:
        timeout = 30

    inherited = _load_cc_connect_feishu_options()
    user_auth = _load_user_auth_state()
    app_id = os.getenv("FEISHU_APP_ID", "").strip() or inherited.get("app_id", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "").strip() or inherited.get("app_secret", "")
    tenant_access_token = os.getenv("FEISHU_TENANT_ACCESS_TOKEN", "").strip() or inherited.get(
        "tenant_access_token", ""
    )
    base_url_raw = os.getenv("FEISHU_BASE_URL", "").strip() or inherited.get("base_url", "https://open.feishu.cn")
    auth_mode = os.getenv("FEISHU_AUTH_MODE", "").strip() or str(user_auth.get("auth_mode", "auto"))
    user_access_token = os.getenv("FEISHU_USER_ACCESS_TOKEN", "").strip() or str(
        user_auth.get("user_access_token", "")
    )
    user_refresh_token = os.getenv("FEISHU_USER_REFRESH_TOKEN", "").strip() or str(
        user_auth.get("user_refresh_token", "")
    )
    user_token_expires_at = _env_int("FEISHU_USER_TOKEN_EXPIRES_AT", int(user_auth.get("user_token_expires_at", 0) or 0))
    user_refresh_expires_at = _env_int(
        "FEISHU_USER_REFRESH_EXPIRES_AT", int(user_auth.get("user_refresh_expires_at", 0) or 0)
    )
    user_open_id = os.getenv("FEISHU_USER_OPEN_ID", "").strip() or str(user_auth.get("user_open_id", ""))

    return FeishuConfig(
        app_id=app_id,
        app_secret=app_secret,
        base_url=base_url_raw.rstrip("/"),
        timeout_seconds=timeout,
        dry_run=_env_bool("FEISHU_DRY_RUN", False),
        tenant_access_token=tenant_access_token,
        auth_mode=auth_mode,
        user_access_token=user_access_token,
        user_refresh_token=user_refresh_token,
        user_token_expires_at=user_token_expires_at,
        user_refresh_expires_at=user_refresh_expires_at,
        user_open_id=user_open_id,
    )


def validate_config(config: FeishuConfig) -> list[str]:
    errors: list[str] = []
    if not config.base_url.startswith("http"):
        errors.append("FEISHU_BASE_URL must start with http/https")
    if config.timeout_seconds <= 0:
        errors.append("FEISHU_TIMEOUT_SECONDS must be > 0")

    auth_mode = config.auth_mode.strip().lower() or "auto"
    if auth_mode not in {"tenant", "user", "auto"}:
        errors.append("FEISHU_AUTH_MODE must be auto, tenant or user")

    if auth_mode == "user":
        if not config.app_id:
            errors.append("FEISHU_APP_ID is required when FEISHU_AUTH_MODE=user")
        if not config.app_secret:
            errors.append("FEISHU_APP_SECRET is required when FEISHU_AUTH_MODE=user")
        if not config.user_refresh_token:
            errors.append("FEISHU_USER_REFRESH_TOKEN is required when FEISHU_AUTH_MODE=user")
        return errors

    if not config.has_static_token:
        if not config.app_id:
            errors.append("FEISHU_APP_ID is required when FEISHU_TENANT_ACCESS_TOKEN is empty")
        if not config.app_secret:
            errors.append("FEISHU_APP_SECRET is required when FEISHU_TENANT_ACCESS_TOKEN is empty")

    return errors
