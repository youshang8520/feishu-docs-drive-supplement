from __future__ import annotations

import mimetypes
from pathlib import Path

from ..client.http import FeishuHttpClient
from ..errors import ValidationError


class UploadService:
    def __init__(self, client: FeishuHttpClient):
        self._client = client

    def upload_file(self, parent_token: str, path: Path, file_name: str | None = None) -> dict:
        if not path.exists() or not path.is_file():
            raise ValidationError(f"Local file not found: {path}")

        content = path.read_bytes()
        name = file_name or path.name
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        return self.upload_bytes(parent_token=parent_token, file_name=name, content=content, mime=mime)

    def upload_bytes(
        self,
        parent_token: str,
        file_name: str,
        content: bytes,
        mime: str = "application/octet-stream",
    ) -> dict:
        if not parent_token.strip():
            raise ValidationError("parent_token is required")
        if not file_name.strip():
            raise ValidationError("file_name is required")

        data = {
            "file_name": file_name,
            "parent_type": "explorer",
            "parent_node": parent_token,
            "size": str(len(content)),
        }
        files = {
            "file": (file_name, content, mime),
        }
        return self._client.post_multipart(
            "/open-apis/drive/v1/files/upload_all",
            data=data,
            files=files,
            auth_preference="user",
        )
