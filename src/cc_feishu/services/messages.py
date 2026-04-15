from __future__ import annotations

import json
from typing import Any

from ..client.http import FeishuHttpClient
from ..errors import ValidationError

_ALLOWED_RECEIVE_ID_TYPES = {"chat_id", "open_id", "user_id", "union_id", "email"}


class MessagesService:
    def __init__(self, client: FeishuHttpClient):
        self._client = client

    def send_text(
        self,
        receive_id: str,
        text: str,
        *,
        receive_id_type: str = "chat_id",
    ) -> dict[str, Any]:
        normalized_receive_id = receive_id.strip()
        if not normalized_receive_id:
            raise ValidationError("receive_id is required")

        normalized_receive_id_type = receive_id_type.strip().lower() or "chat_id"
        if normalized_receive_id_type not in _ALLOWED_RECEIVE_ID_TYPES:
            allowed = ", ".join(sorted(_ALLOWED_RECEIVE_ID_TYPES))
            raise ValidationError(f"receive_id_type must be one of: {allowed}")

        normalized_text = text.strip()
        if not normalized_text:
            raise ValidationError("text is required")

        return self._client.post(
            f"/open-apis/im/v1/messages?receive_id_type={normalized_receive_id_type}",
            json_data={
                "receive_id": normalized_receive_id,
                "msg_type": "text",
                "content": json.dumps({"text": normalized_text}, ensure_ascii=False),
            },
            auth_preference="tenant",
        )
