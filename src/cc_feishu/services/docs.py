from __future__ import annotations

from ..client.http import FeishuHttpClient


class DocsService:
    def __init__(self, client: FeishuHttpClient):
        self._client = client

    def create(self, title: str, folder_token: str | None = None) -> dict:
        payload: dict = {"title": title}
        if folder_token:
            payload["folder_token"] = folder_token
        return self._client.post("/open-apis/docx/v1/documents", json_data=payload)

    def read(self, doc_token: str) -> dict:
        return self._client.get(f"/open-apis/docx/v1/documents/{doc_token}")

    def list_blocks(self, doc_token: str) -> dict:
        return self._client.get(f"/open-apis/docx/v1/documents/{doc_token}/blocks")

    def _get_root_block_id(self, doc_token: str) -> str:
        if self._client._config.dry_run:
            return doc_token
        res = self.list_blocks(doc_token)
        items = ((res.get("data") or {}).get("items") or [])
        for item in items:
            if item.get("parent_id") == "":
                block_id = item.get("block_id")
                if block_id:
                    return str(block_id)
        return doc_token

    def _append_children(self, doc_token: str, children: list[dict], *, index: int | None = None) -> dict:
        root_block_id = self._get_root_block_id(doc_token)
        payload: dict = {"children": children}
        if index is not None:
            payload["index"] = index
        return self._client.post(
            f"/open-apis/docx/v1/documents/{doc_token}/blocks/{root_block_id}/children",
            json_data=payload,
        )

    def append_text(self, doc_token: str, text: str) -> dict:
        return self._append_children(
            doc_token,
            [
                {
                    "block_type": 2,
                    "text": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": text,
                                }
                            }
                        ]
                    },
                }
            ],
        )

    def append_heading(self, doc_token: str, text: str, *, level: int = 1, index: int | None = None) -> dict:
        block_type = 3 if level == 1 else 4
        heading_key = "heading1" if level == 1 else "heading2"
        return self._append_children(
            doc_token,
            [
                {
                    "block_type": block_type,
                    heading_key: {
                        "elements": [
                            {
                                "text_run": {
                                    "content": text,
                                }
                            }
                        ]
                    },
                }
            ],
            index=index,
        )

    def append_bullet(self, doc_token: str, text: str, *, index: int | None = None) -> dict:
        return self._append_children(
            doc_token,
            [
                {
                    "block_type": 12,
                    "bullet": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": text,
                                }
                            }
                        ]
                    },
                }
            ],
            index=index,
        )

    def append_styled_text(
        self,
        doc_token: str,
        text: str,
        *,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        index: int | None = None,
    ) -> dict:
        return self._append_children(
            doc_token,
            [
                {
                    "block_type": 2,
                    "text": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": text,
                                    "text_element_style": {
                                        "bold": bold,
                                        "italic": italic,
                                        "underline": underline,
                                    },
                                }
                            }
                        ]
                    },
                }
            ],
            index=index,
        )

    def update_block_text(self, doc_token: str, block_id: str, text: str) -> dict:
        payload = {
            "update_text_elements": {
                "elements": [
                    {
                        "text_run": {
                            "content": text,
                        }
                    }
                ]
            }
        }
        return self._client.patch(
            f"/open-apis/docx/v1/documents/{doc_token}/blocks/{block_id}",
            json_data=payload,
        )

    def update_text(self, doc_token: str, text: str, block_id: str | None = None) -> dict:
        if block_id:
            return self.update_block_text(doc_token, block_id, text)
        return self.append_text(doc_token, text)

    def delete(self, doc_token: str) -> dict:
        return self._client.delete(f"/open-apis/drive/v1/files/{doc_token}", params={"type": "docx"})
