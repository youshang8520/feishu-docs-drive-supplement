from __future__ import annotations

import re
from urllib.parse import quote

from ..client.http import FeishuHttpClient
from ..errors import ValidationError


class SheetsService:
    def __init__(self, client: FeishuHttpClient):
        self._client = client

    def _resolve_sheet_id(self, sheet_token: str) -> str:
        res = self._client.get(
            f"/open-apis/sheets/v3/spreadsheets/{sheet_token}/sheets/query",
            auth_preference="user",
        )
        sheets = ((res.get("data") or {}).get("sheets") or [])
        for item in sheets:
            sheet_id = item.get("sheet_id") or item.get("sheetId")
            if sheet_id:
                return str(sheet_id)
        raise ValidationError("sheetId not found")

    def _normalize_a1_range(self, sheet_token: str, a1_range: str) -> str:
        if "!" in a1_range:
            return a1_range
        if self._client._config.dry_run:
            return a1_range
        return f"{self._resolve_sheet_id(sheet_token)}!{a1_range}"

    def _column_index(self, letters: str) -> int:
        value = 0
        for char in letters.upper():
            value = value * 26 + (ord(char) - ord("A") + 1)
        return value

    def _empty_values_for_range(self, a1_range: str) -> list[list[str]]:
        range_part = a1_range.split("!", 1)[-1]
        if ":" in range_part:
            start, end = range_part.split(":", 1)
        else:
            start = end = range_part

        pattern = re.compile(r"^([A-Za-z]+)(\d+)$")
        m1 = pattern.match(start)
        m2 = pattern.match(end)
        if not m1 or not m2:
            return [[""]]

        start_col, start_row = self._column_index(m1.group(1)), int(m1.group(2))
        end_col, end_row = self._column_index(m2.group(1)), int(m2.group(2))

        rows = max(abs(end_row - start_row) + 1, 1)
        cols = max(abs(end_col - start_col) + 1, 1)
        return [["" for _ in range(cols)] for _ in range(rows)]

    def create(self, title: str, folder_token: str | None = None) -> dict:
        payload: dict = {"title": title}
        if folder_token:
            payload["folder_token"] = folder_token
        return self._client.post(
            "/open-apis/sheets/v3/spreadsheets",
            json_data=payload,
            auth_preference="user",
        )

    def read_range(self, sheet_token: str, a1_range: str) -> dict:
        normalized = self._normalize_a1_range(sheet_token, a1_range)
        encoded = quote(normalized, safe="")
        return self._client.get(
            f"/open-apis/sheets/v2/spreadsheets/{sheet_token}/values/{encoded}",
            auth_preference="user",
        )

    def write_range(self, sheet_token: str, a1_range: str, values: list[list]) -> dict:
        normalized = self._normalize_a1_range(sheet_token, a1_range)
        payload = {
            "valueRange": {
                "range": normalized,
                "values": values,
            }
        }
        return self._client.put(
            f"/open-apis/sheets/v2/spreadsheets/{sheet_token}/values",
            json_data=payload,
            auth_preference="user",
        )

    def append_rows(self, sheet_token: str, a1_range: str, values: list[list]) -> dict:
        normalized = self._normalize_a1_range(sheet_token, a1_range)
        payload = {
            "valueRange": {
                "range": normalized,
                "values": values,
            }
        }
        return self._client.post(
            f"/open-apis/sheets/v2/spreadsheets/{sheet_token}/values_append",
            json_data=payload,
            auth_preference="user",
        )

    def delete_range(self, sheet_token: str, a1_range: str) -> dict:
        normalized = self._normalize_a1_range(sheet_token, a1_range)
        payload = {
            "valueRanges": [
                {
                    "range": normalized,
                    "values": self._empty_values_for_range(normalized),
                }
            ]
        }
        return self._client.post(
            f"/open-apis/sheets/v2/spreadsheets/{sheet_token}/values_batch_update",
            json_data=payload,
            auth_preference="user",
        )
