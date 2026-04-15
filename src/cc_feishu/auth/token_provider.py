import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ..config import FeishuConfig, save_user_auth_state
from ..errors import AuthError, ValidationError


class FeishuTokenProvider:
    def __init__(self, config: FeishuConfig):
        self._config = config
        self._cached_token: str = ""
        self._expires_at: float = 0

    def validate_env(self) -> list[str]:
        errors: list[str] = []
        if self._config.auth_mode.strip().lower() == "user":
            if not self._config.app_id:
                errors.append("FEISHU_APP_ID is missing")
            if not self._config.app_secret:
                errors.append("FEISHU_APP_SECRET is missing")
            if not self._config.user_refresh_token:
                errors.append("FEISHU_USER_REFRESH_TOKEN is missing")
            return errors

        if self._config.has_static_token:
            return errors
        if not self._config.app_id:
            errors.append("FEISHU_APP_ID is missing")
        if not self._config.app_secret:
            errors.append("FEISHU_APP_SECRET is missing")
        return errors

    def _is_transient_network_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        markers = (
            "timeout",
            "timed out",
            "temporarily unavailable",
            "connection reset",
            "connection aborted",
            "connection refused",
            "remote end closed connection",
            "unexpected_eof_while_reading",
            "unexpected eof",
            "ssleoferror",
            "eof occurred in violation of protocol",
            "max retries exceeded",
        )
        return any(marker in message for marker in markers)

    def _require_app_credentials(self) -> None:
        if not self._config.app_id or not self._config.app_secret:
            raise ValidationError("FEISHU_APP_ID is missing; FEISHU_APP_SECRET is missing")

    def _normalize_scope(self, scope: str) -> str:
        parts = [item.strip() for item in scope.replace(",", " ").split() if item.strip()]
        if "offline_access" not in parts:
            parts.append("offline_access")
        if not parts:
            raise ValidationError("At least one scope is required for user auth")
        return " ".join(parts)

    def _open_json(self, req: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="ignore")
        except urllib.error.URLError as exc:
            raise AuthError(f"Feishu auth request failed: {exc}") from exc

        try:
            data: dict[str, Any] = json.loads(raw)
        except ValueError as exc:
            raise AuthError(f"Feishu auth returned invalid JSON: {raw[:200]}") from exc
        return data

    def _post_form_json(self, url: str, form: dict[str, str], headers: dict[str, str] | None = None) -> dict[str, Any]:
        body = urllib.parse.urlencode(form).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded", **(headers or {})},
            method="POST",
        )
        return self._open_json(req)

    def _get_json(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        req = urllib.request.Request(url, headers=headers or {}, method="GET")
        return self._open_json(req)

    def has_user_token(self) -> bool:
        return self._config.has_user_refresh_token or bool(self._config.user_access_token.strip())

    def start_device_authorization(self, scope: str) -> dict[str, Any]:
        self._require_app_credentials()
        normalized_scope = self._normalize_scope(scope)
        basic_auth = base64.b64encode(f"{self._config.app_id}:{self._config.app_secret}".encode("utf-8")).decode("ascii")
        data = self._post_form_json(
            "https://accounts.feishu.cn/oauth/v1/device_authorization",
            {"client_id": self._config.app_id, "scope": normalized_scope},
            headers={"Authorization": f"Basic {basic_auth}"},
        )
        if data.get("code") not in (None, 0):
            raise AuthError(f"Device authorization failed: {data.get('msg') or data}")
        if not data.get("device_code"):
            raise AuthError("Device authorization response missing device_code")
        return data

    def get_user_info(self, access_token: str) -> dict[str, Any]:
        data = self._get_json(
            f"{self._config.base_url}/open-apis/authen/v1/user_info",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if data.get("code") not in (None, 0):
            raise AuthError(f"Fetch user info failed: {data.get('msg') or data}")
        return data.get("data") or {}

    def poll_device_authorization(
        self,
        device_code: str,
        *,
        interval_seconds: int = 5,
        timeout_seconds: int = 600,
        auth_mode: str = "user",
    ) -> dict[str, Any]:
        self._require_app_credentials()
        deadline = time.time() + max(1, timeout_seconds)
        wait_seconds = max(1, interval_seconds)

        while time.time() < deadline:
            data = self._post_form_json(
                f"{self._config.base_url}/open-apis/authen/v2/oauth/token",
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                    "client_id": self._config.app_id,
                    "client_secret": self._config.app_secret,
                },
            )

            if data.get("code") in (None, 0) and data.get("access_token"):
                token = (data.get("access_token") or "").strip()
                refresh_token = (data.get("refresh_token") or "").strip()
                expires_in = int(data.get("expires_in") or 7200)
                refresh_expires_in = int(data.get("refresh_token_expires_in") or 604800)
                user_info = self.get_user_info(token)
                updated = FeishuConfig(
                    app_id=self._config.app_id,
                    app_secret=self._config.app_secret,
                    base_url=self._config.base_url,
                    timeout_seconds=self._config.timeout_seconds,
                    dry_run=self._config.dry_run,
                    tenant_access_token=self._config.tenant_access_token,
                    auth_mode=auth_mode,
                    user_access_token=token,
                    user_refresh_token=refresh_token,
                    user_token_expires_at=int(time.time()) + expires_in,
                    user_refresh_expires_at=int(time.time()) + refresh_expires_in,
                    user_open_id=str(user_info.get("open_id") or data.get("open_id") or "").strip(),
                )
                save_user_auth_state(updated)
                self._config = updated
                return {
                    "ok": True,
                    "auth_mode": updated.auth_mode,
                    "user_open_id": updated.user_open_id,
                    "has_user_access_token": bool(updated.user_access_token),
                    "has_user_refresh_token": bool(updated.user_refresh_token),
                    "user_token_expires_at": updated.user_token_expires_at,
                    "user_refresh_expires_at": updated.user_refresh_expires_at,
                    "user_info": user_info,
                }

            error = str(data.get("error") or "").strip().lower()
            message = str(data.get("error_description") or data.get("msg") or "").strip().lower()
            if error in {"authorization_pending"} or "authorization pending" in message:
                time.sleep(wait_seconds)
                continue
            if error in {"slow_down"} or "slow down" in message:
                wait_seconds += 5
                time.sleep(wait_seconds)
                continue
            if error in {"access_denied", "expired_token"}:
                raise AuthError(str(data.get("error_description") or data.get("msg") or error))
            if data.get("code") not in (None, 0):
                raise AuthError(f"Device token polling failed: {data.get('msg') or data}")
            raise AuthError(f"Device token polling failed: {data}")

        raise AuthError("Timed out waiting for Feishu user authorization")

    def get_tenant_token(self, force_refresh: bool = False) -> str:
        if self._config.has_static_token:
            return self._config.tenant_access_token

        if not force_refresh and self._cached_token and time.time() < self._expires_at - 60:
            return self._cached_token

        errors = self.validate_env()
        if errors and self._config.auth_mode.strip().lower() != "auto":
            raise ValidationError("; ".join(errors))
        if not self._config.app_id or not self._config.app_secret:
            raise ValidationError("FEISHU_APP_ID is missing; FEISHU_APP_SECRET is missing")

        url = f"{self._config.base_url}/open-apis/auth/v3/tenant_access_token/internal"
        body = json.dumps(
            {
                "app_id": self._config.app_id,
                "app_secret": self._config.app_secret,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8", "Content-Length": str(len(body))}

        delay = 0.5
        last_exc: Exception | None = None
        for attempt in range(1, 5):
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self._config.timeout_seconds) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8", errors="ignore")
                raise AuthError(f"Tenant token API failed: {raw}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = exc
                if attempt >= 4 or not self._is_transient_network_error(exc):
                    break
                time.sleep(delay)
                delay = min(delay * 2, 5.0)
                continue

            try:
                data: dict[str, Any] = json.loads(raw)
            except ValueError as exc:
                raise AuthError(f"Tenant token API returned invalid JSON: {raw[:200]}") from exc

            if data.get("code") != 0:
                raise AuthError(f"Tenant token API failed: {data.get('msg') or data}")

            token = (data.get("tenant_access_token") or "").strip()
            expires_in = int(data.get("expire") or 7200)
            if not token:
                raise AuthError("Tenant token missing from response")

            self._cached_token = token
            self._expires_at = time.time() + max(60, expires_in)
            return token

        raise AuthError(f"Failed to get tenant token: {last_exc}") from last_exc

    def get_user_token(self, force_refresh: bool = False) -> str:
        if not self._config.app_id or not self._config.app_secret:
            raise ValidationError("FEISHU_APP_ID is missing; FEISHU_APP_SECRET is missing")
        if not self._config.user_refresh_token:
            raise ValidationError("FEISHU_USER_REFRESH_TOKEN is missing")

        now = int(time.time())
        if not force_refresh and self._config.user_access_token and now < self._config.user_token_expires_at - 60:
            return self._config.user_access_token

        url = f"{self._config.base_url}/open-apis/authen/v2/oauth/token"
        body = urllib.parse.urlencode(
            {
                "grant_type": "refresh_token",
                "refresh_token": self._config.user_refresh_token,
                "client_id": self._config.app_id,
                "client_secret": self._config.app_secret,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="ignore")
            raise AuthError(f"User token refresh failed: {raw}") from exc
        except urllib.error.URLError as exc:
            raise AuthError(f"User token refresh failed: {exc}") from exc

        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise AuthError(f"User token refresh returned invalid JSON: {raw[:200]}") from exc

        if data.get("code") not in (None, 0):
            raise AuthError(f"User token refresh failed: {data.get('msg') or data}")

        token = (data.get("access_token") or "").strip()
        refresh_token = (data.get("refresh_token") or self._config.user_refresh_token).strip()
        expires_in = int(data.get("expires_in") or 7200)
        refresh_expires_in = int(data.get("refresh_token_expires_in") or 604800)
        if not token:
            raise AuthError("User token refresh returned empty access_token")

        updated = FeishuConfig(
            app_id=self._config.app_id,
            app_secret=self._config.app_secret,
            base_url=self._config.base_url,
            timeout_seconds=self._config.timeout_seconds,
            dry_run=self._config.dry_run,
            tenant_access_token=self._config.tenant_access_token,
            auth_mode=self._config.auth_mode,
            user_access_token=token,
            user_refresh_token=refresh_token,
            user_token_expires_at=now + expires_in,
            user_refresh_expires_at=now + refresh_expires_in,
            user_open_id=self._config.user_open_id,
        )
        save_user_auth_state(updated)
        self._config = updated
        return token
