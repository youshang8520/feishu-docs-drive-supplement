from __future__ import annotations

from ..client.http import FeishuHttpClient


class SlidesService:
    def __init__(self, client: FeishuHttpClient):
        self._client = client

    def create(self, title: str, folder_token: str | None = None) -> dict:
        payload: dict = {"title": title}
        if folder_token:
            payload["folder_token"] = folder_token
        return self._client.post("/open-apis/slides/v1/presentations", json_data=payload)

    def read(self, slides_token: str) -> dict:
        return self._client.get(f"/open-apis/slides/v1/presentations/{slides_token}")

    def append_slide(self, slides_token: str, title: str) -> dict:
        payload = {
            "requests": [
                {
                    "createSlide": {
                        "slideLayoutReference": {"predefinedLayout": "BLANK"},
                    }
                },
                {
                    "createShape": {
                        "shapeType": "TEXT_BOX",
                        "elementProperties": {
                            "pageObjectId": "{{new_slide_id}}",
                        },
                        "text": title,
                    }
                },
            ]
        }
        return self._client.post(
            f"/open-apis/slides/v1/presentations/{slides_token}:batchUpdate",
            json_data=payload,
        )

    def update_slide(self, slides_token: str, slide_id: str, title: str) -> dict:
        payload = {
            "requests": [
                {
                    "updateShapeText": {
                        "objectId": slide_id,
                        "text": title,
                    }
                }
            ]
        }
        return self._client.post(
            f"/open-apis/slides/v1/presentations/{slides_token}:batchUpdate",
            json_data=payload,
        )

    def delete_slide(self, slides_token: str, slide_id: str) -> dict:
        payload = {
            "requests": [
                {
                    "deleteObject": {
                        "objectId": slide_id,
                    }
                }
            ]
        }
        return self._client.post(
            f"/open-apis/slides/v1/presentations/{slides_token}:batchUpdate",
            json_data=payload,
        )
