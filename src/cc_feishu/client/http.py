from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any
from uuid import uuid4

from ..auth.token_provider import FeishuTokenProvider
from ..config import FeishuConfig
from ..errors import (
    AuthError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    TransientApiError,
    ValidationError,
)


class FeishuHttpClient:
    def __init__(self, config: FeishuConfig, token_provider: FeishuTokenProvider):
        self._config = config
        self._token_provider = token_provider

    def _get_bearer_token(self, auth_preference: str = "auto") -> str:
        preferred = auth_preference.strip().lower() or "auto"
        if preferred == "user":
            return self._token_provider.get_user_token()
        if preferred == "tenant":
            return self._token_provider.get_tenant_token()

        mode = self._config.auth_mode.strip().lower() or "auto"
        if mode == "user":
            return self._token_provider.get_user_token()
        if mode == "tenant":
            return self._token_provider.get_tenant_token()
        if self._token_provider.has_user_token():
            return self._token_provider.get_user_token()
        return self._token_provider.get_tenant_token()

    def validate_connectivity(self) -> dict[str, Any]:
        token = self._get_bearer_token()
        return {
            "ok": True,
            "token_preview": token[:8] + "..." if len(token) > 8 else "***",
            "base_url": self._config.base_url,
            "auth_mode": self._config.auth_mode,
        }

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        auth_preference: str = "auto",
    ) -> dict[str, Any]:
        return self._request("GET", path, params=params, auth_preference=auth_preference)

    def post(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
        *,
        auth_preference: str = "auto",
    ) -> dict[str, Any]:
        return self._request("POST", path, json_data=json_data, auth_preference=auth_preference)

    def patch(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
        *,
        auth_preference: str = "auto",
    ) -> dict[str, Any]:
        return self._request("PATCH", path, json_data=json_data, auth_preference=auth_preference)

    def put(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
        *,
        auth_preference: str = "auto",
    ) -> dict[str, Any]:
        return self._request("PUT", path, json_data=json_data, auth_preference=auth_preference)

    def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        *,
        auth_preference: str = "auto",
    ) -> dict[str, Any]:
        return self._request("DELETE", path, params=params, json_data=json_data, auth_preference=auth_preference)

    def post_multipart(
        self,
        path: str,
        data: dict[str, Any],
        files: dict[str, tuple[str, bytes, str]],
        *,
        auth_preference: str = "auto",
    ) -> dict[str, Any]:
        url = self._build_url(path)

        if self._config.dry_run:
            return {
                "dry_run": True,
                "method": "POST",
                "url": url,
                "data": data,
                "files": list(files.keys()),
            }

        token = self._get_bearer_token(auth_preference=auth_preference)
        boundary = f"----cc-feishu-{uuid4().hex}"
        body = self._encode_multipart(data, files, boundary)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        return self._open_json(req)

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._config.base_url}{path}"

    def _encode_params(self, params: dict[str, Any] | None) -> str:
        if not params:
            return ""
        pairs: list[tuple[str, str]] = []
        for key, value in params.items():
            if value is None:
                continue
            pairs.append((key, str(value)))
        return urllib.parse.urlencode(pairs)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        retries: int = 3,
        auth_preference: str = "auto",
    ) -> dict[str, Any]:
        url = self._build_url(path)
        query = self._encode_params(params)
        if query:
            joiner = "&" if "?" in url else "?"
            url = f"{url}{joiner}{query}"

        if self._config.dry_run and method in {"POST", "PATCH", "PUT", "DELETE"}:
            return {
                "dry_run": True,
                "method": method,
                "url": url,
                "params": params,
                "json": json_data,
            }

        token = self._get_bearer_token(auth_preference=auth_preference)
        data: bytes | None = None
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        if json_data is not None:
            data = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
            headers["Content-Length"] = str(len(data))

        for attempt in range(1, retries + 1):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                return self._open_json(req)
            except RateLimitError:
                if attempt >= retries:
                    raise
                time.sleep(min(2**attempt, 8))
            except TransientApiError:
                if attempt >= retries:
                    raise
                time.sleep(min(2**attempt, 8))

        raise ValidationError("request retries exhausted")

    def _open_json(self, req: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout_seconds) as resp:
                status = resp.status
                raw = resp.read().decode("utf-8", errors="ignore")
                return self._handle_response(status, raw)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="ignore")
            return self._handle_response(exc.code, raw)
        except urllib.error.URLError as exc:
            raise TransientApiError(f"Network failure for {req.full_url}: {exc}") from exc
        except TimeoutError as exc:
            raise TransientApiError(f"Timeout when calling {req.full_url}") from exc

    def _handle_response(self, status: int, raw: str) -> dict[str, Any]:
        try:
            data: dict[str, Any] = json.loads(raw)
        except ValueError as exc:
            raise TransientApiError(f"Invalid JSON response: {raw[:200]}") from exc

        if status == 401:
            raise AuthError(data.get("msg") or "Unauthorized")
        if status == 403:
            raise PermissionDeniedError(data.get("msg") or "Forbidden")
        if status == 404:
            raise NotFoundError(data.get("msg") or "Not found")
        if status == 409:
            raise ConflictError(data.get("msg") or "Conflict")
        if status == 429:
            raise RateLimitError(data.get("msg") or "Rate limited")
        if status >= 500:
            raise TransientApiError(data.get("msg") or f"Server error {status}")

        if data.get("code") not in (None, 0):
            code = int(data.get("code") or -1)
            message = data.get("msg") or data
            if code in {99991663, 1254290}:
                raise RateLimitError(str(message))
            if code in {99991664, 1254302}:
                raise PermissionDeniedError(str(message))
            raise ValidationError(str(message))

        return data

    def _encode_multipart(
        self,
        data: dict[str, Any],
        files: dict[str, tuple[str, bytes, str]],
        boundary: str,
    ) -> bytes:
        parts: list[bytes] = []
        for key, value in data.items():
            parts.extend(
                [
                    f"--{boundary}\r\n".encode(),
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                    str(value).encode("utf-8"),
                    b"\r\n",
                ]
            )

        for key, (filename, content, mime) in files.items():
            parts.extend(
                [
                    f"--{boundary}\r\n".encode(),
                    (
                        f'Content-Disposition: form-data; name="{key}"; '
                        f'filename="{filename}"\r\n'
                    ).encode(),
                    f"Content-Type: {mime}\r\n\r\n".encode(),
                    content,
                    b"\r\n",
                ]
            )

        parts.append(f"--{boundary}--\r\n".encode())
        return b"".join(parts)
