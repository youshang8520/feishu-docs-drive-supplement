from __future__ import annotations

from ..client.http import FeishuHttpClient


class BitableService:
    def __init__(self, client: FeishuHttpClient):
        self._client = client

    def list_tables(self, app_token: str) -> dict:
        return self._client.get(f"/open-apis/bitable/v1/apps/{app_token}/tables", auth_preference="user")

    def list_fields(self, app_token: str, table_id: str) -> dict:
        return self._client.get(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
            auth_preference="user",
        )

    def create_table(self, app_token: str, table_name: str) -> dict:
        payload = {
            "table": {
                "name": table_name,
            }
        }
        return self._client.post(
            f"/open-apis/bitable/v1/apps/{app_token}/tables",
            json_data=payload,
            auth_preference="user",
        )

    def read_records(self, app_token: str, table_id: str, view_id: str | None = None) -> dict:
        params: dict = {}
        if view_id:
            params["view_id"] = view_id
        return self._client.get(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
            params=params,
            auth_preference="user",
        )

    def create_record(self, app_token: str, table_id: str, fields: dict) -> dict:
        payload = {
            "records": [
                {
                    "fields": fields,
                }
            ]
        }
        return self._client.post(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
            json_data=payload,
            auth_preference="user",
        )

    def update_record(self, app_token: str, table_id: str, record_id: str, fields: dict) -> dict:
        payload = {
            "fields": fields,
        }
        return self._client.put(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            json_data=payload,
            auth_preference="user",
        )

    def delete_record(self, app_token: str, table_id: str, record_id: str) -> dict:
        return self._client.delete(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            json_data={},
            auth_preference="user",
        )
