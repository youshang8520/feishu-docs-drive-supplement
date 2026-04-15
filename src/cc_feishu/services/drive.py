from __future__ import annotations

from typing import Any

from ..client.http import FeishuHttpClient
from ..errors import ValidationError


class DriveService:
    def __init__(self, client: FeishuHttpClient):
        self._client = client

    def list_folder(self, folder_token: str | None = None, page_token: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {
            "page_size": 50,
        }
        # Only add folder_token if it's provided and not "root"
        # Feishu API lists root directory when folder_token is omitted
        if folder_token and folder_token.lower() != "root":
            params["folder_token"] = folder_token
        if page_token:
            params["page_token"] = page_token
        return self._client.get("/open-apis/drive/v1/files", params=params, auth_preference="user")

    def create_folder(self, parent_token: str, name: str, request_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "folder_token": parent_token,
        }
        if request_id:
            payload["request_id"] = request_id
        return self._client.post(
            "/open-apis/drive/v1/files/create_folder",
            json_data=payload,
            auth_preference="user",
        )

    def read_file_meta(self, file_token: str) -> dict[str, Any]:
        payload = {
            "request_docs": [
                {
                    "doc_token": file_token,
                    "doc_type": "file",
                }
            ]
        }
        return self._client.post(
            "/open-apis/drive/v1/metas/batch_query",
            json_data=payload,
            auth_preference="user",
        )

    def update_file_meta(
        self,
        file_token: str,
        *,
        name: str | None = None,
        folder_token: str | None = None,
    ) -> dict[str, Any]:
        if name:
            raise ValidationError("Drive rename is not available for current API route")
        if not folder_token:
            raise ValidationError("Either folder_token or name is required")
        payload: dict[str, Any] = {
            "type": "file",
            "folder_token": folder_token,
        }
        return self._client.post(
            f"/open-apis/drive/v1/files/{file_token}/move",
            json_data=payload,
            auth_preference="user",
        )

    def delete_node(
        self,
        token: str,
        recursive: bool = False,
        request_id: str | None = None,
        node_type: str = "file",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "type": node_type,
            "recursive": recursive,
        }
        if request_id:
            params["request_id"] = request_id
        return self._client.delete(
            f"/open-apis/drive/v1/files/{token}",
            params=params,
            auth_preference="user",
        )

    def move_node(
        self,
        token: str,
        target_folder_token: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "file",
            "folder_token": target_folder_token,
        }
        if request_id:
            payload["request_id"] = request_id
        return self._client.post(
            f"/open-apis/drive/v1/files/{token}/move",
            json_data=payload,
            auth_preference="user",
        )
