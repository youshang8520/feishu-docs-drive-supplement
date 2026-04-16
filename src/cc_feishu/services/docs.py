from __future__ import annotations

from ..client.http import FeishuHttpClient
from ..errors import ValidationError


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
            auth_preference="user",
        )

    def append_blocks(self, doc_token: str, children: list[dict], *, index: int | None = None) -> dict:
        return self._append_children(doc_token, children, index=index)

    def _text_elements(
        self,
        text: str,
        *,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
    ) -> list[dict]:
        text_run: dict = {"content": text}
        if bold or italic or underline:
            text_run["text_element_style"] = {
                "bold": bold,
                "italic": italic,
                "underline": underline,
            }
        return [{"text_run": text_run}]

    def _text_block(
        self,
        text: str,
        *,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
    ) -> dict:
        return {
            "block_type": 2,
            "text": {
                "elements": self._text_elements(
                    text,
                    bold=bold,
                    italic=italic,
                    underline=underline,
                )
            },
        }

    def _heading_block(self, text: str, *, level: int = 1) -> dict:
        if level not in {1, 2}:
            raise ValidationError("heading level must be 1 or 2")
        block_type = 3 if level == 1 else 4
        heading_key = "heading1" if level == 1 else "heading2"
        return {
            "block_type": block_type,
            heading_key: {
                "elements": self._text_elements(text),
            },
        }

    def _bullet_block(self, text: str) -> dict:
        return {
            "block_type": 12,
            "bullet": {
                "elements": self._text_elements(text),
            },
        }

    def _code_block(self, text: str, *, language: int = 49, wrap: bool = True) -> dict:
        return {
            "block_type": 14,
            "code": {
                "elements": self._text_elements(text),
                "style": {
                    "language": language,
                    "wrap": wrap,
                },
            },
        }

    def append_text(self, doc_token: str, text: str) -> dict:
        return self._append_children(doc_token, [self._text_block(text)])

    def append_heading(self, doc_token: str, text: str, *, level: int = 1, index: int | None = None) -> dict:
        return self._append_children(doc_token, [self._heading_block(text, level=level)], index=index)

    def append_bullet(self, doc_token: str, text: str, *, index: int | None = None) -> dict:
        return self._append_children(doc_token, [self._bullet_block(text)], index=index)

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
                self._text_block(
                    text,
                    bold=bold,
                    italic=italic,
                    underline=underline,
                )
            ],
            index=index,
        )

    def append_code_block(
        self,
        doc_token: str,
        text: str,
        *,
        language: int = 49,
        wrap: bool = True,
        index: int | None = None,
    ) -> dict:
        return self._append_children(
            doc_token,
            [self._code_block(text, language=language, wrap=wrap)],
            index=index,
        )

    def append_rich_text(self, doc_token: str, blocks: list[dict], *, index: int | None = None) -> dict:
        children: list[dict] = []
        for block in blocks:
            block_type = str(block.get("type") or "").strip().lower()
            text = str(block.get("text") or "")
            if not block_type:
                raise ValidationError("rich text block type is required")
            if block_type in {"paragraph", "text"}:
                children.append(
                    self._text_block(
                        text,
                        bold=bool(block.get("bold", False)),
                        italic=bool(block.get("italic", False)),
                        underline=bool(block.get("underline", False)),
                    )
                )
            elif block_type == "heading":
                children.append(self._heading_block(text, level=int(block.get("level", 1) or 1)))
            elif block_type == "bullet":
                children.append(self._bullet_block(text))
            elif block_type == "code":
                children.append(
                    self._code_block(
                        text,
                        language=int(block.get("language", 49) or 49),
                        wrap=bool(block.get("wrap", True)),
                    )
                )
            else:
                raise ValidationError(f"unsupported rich text block type: {block_type}")
        return self._append_children(doc_token, children, index=index)

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
            auth_preference="user",
        )

    def update_text(self, doc_token: str, text: str, block_id: str | None = None) -> dict:
        if block_id:
            return self.update_block_text(doc_token, block_id, text)
        return self.append_text(doc_token, text)

    def delete(self, doc_token: str) -> dict:
        return self._client.delete(f"/open-apis/drive/v1/files/{doc_token}", params={"type": "docx"}, auth_preference="user")
