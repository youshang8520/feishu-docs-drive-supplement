from cc_feishu.config import FeishuConfig
from cc_feishu.auth.token_provider import FeishuTokenProvider
from cc_feishu.client.http import FeishuHttpClient
from cc_feishu.errors import ValidationError
from cc_feishu.services.drive import DriveService
from cc_feishu.services.docs import DocsService
from cc_feishu.services.sheets import SheetsService
from cc_feishu.services.slides import SlidesService
from cc_feishu.services.bitable import BitableService
from cc_feishu.services.upload import UploadService
from cc_feishu.mcp.tools import TOOLS


def _client():
    cfg = FeishuConfig(
        app_id="",
        app_secret="",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
        dry_run=True,
        tenant_access_token="token",
    )
    provider = FeishuTokenProvider(cfg)
    return FeishuHttpClient(cfg, provider)


def test_drive_create_folder_dry_run():
    svc = DriveService(_client())
    res = svc.create_folder("fld", "demo")
    assert res["dry_run"] is True
    assert res["method"] == "POST"


def test_drive_read_file_meta_uses_batch_query():
    svc = DriveService(_client())
    res = svc.read_file_meta("file_tok")
    assert res["dry_run"] is True
    assert res["method"] == "POST"
    assert res["url"].endswith("/open-apis/drive/v1/metas/batch_query")
    assert res["json"] == {
        "request_docs": [
            {
                "doc_token": "file_tok",
                "doc_type": "file",
            }
        ]
    }


def test_drive_update_file_meta_moves_file_when_folder_given():
    svc = DriveService(_client())
    res = svc.update_file_meta("file_tok", folder_token="folder_tok")
    assert res["dry_run"] is True
    assert res["method"] == "POST"
    assert res["url"].endswith("/open-apis/drive/v1/files/file_tok/move")
    assert res["json"] == {"type": "file", "folder_token": "folder_tok"}


def test_drive_update_file_meta_rejects_rename():
    svc = DriveService(_client())
    try:
        svc.update_file_meta("file_tok", name="new_name")
        assert False, "expected ValidationError"
    except ValidationError as exc:
        assert "rename" in str(exc)


def test_drive_update_file_meta_requires_any_field():
    svc = DriveService(_client())
    try:
        svc.update_file_meta("file_tok")
        assert False, "expected ValidationError"
    except ValidationError as exc:
        assert "Either folder_token or name is required" in str(exc)


def test_docs_append_dry_run():
    svc = DocsService(_client())
    res = svc.append_text("doc", "hello")
    assert res["dry_run"] is True


def test_docs_update_block_uses_patch_when_block_id_is_given():
    class _Client:
        def patch(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"path": path, "json": json_data, "auth_preference": auth_preference}

    svc = DocsService(_Client())
    res = svc.update_text("doc_tok", "updated", block_id="blk_tok")

    assert res["path"].endswith("/open-apis/docx/v1/documents/doc_tok/blocks/blk_tok")
    assert res["json"] == {
        "update_text_elements": {
            "elements": [
                {
                    "text_run": {
                        "content": "updated",
                    }
                }
            ]
        }
    }
    assert res["auth_preference"] == "user"


def test_docs_list_blocks_uses_document_blocks_endpoint():
    class _Client:
        def get(self, path: str, params=None, *, auth_preference="auto"):
            return {"path": path, "auth_preference": auth_preference}

    svc = DocsService(_Client())
    res = svc.list_blocks("doc_tok")

    assert res["path"].endswith("/open-apis/docx/v1/documents/doc_tok/blocks")




def test_docs_append_heading_uses_heading_block_payload():
    class _Client:
        class _Config:
            dry_run = True

        def __init__(self):
            self._config = self._Config()

        def post(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"path": path, "json": json_data, "auth_preference": auth_preference}

    svc = DocsService(_Client())
    res = svc.append_heading("doc_tok", "Heading", level=1, index=0)

    assert res["json"] == {
        "children": [
            {
                "block_type": 3,
                "heading1": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "Heading",
                            }
                        }
                    ]
                },
            }
        ],
        "index": 0,
    }


def test_docs_append_bullet_uses_bullet_block_payload():
    class _Client:
        class _Config:
            dry_run = True

        def __init__(self):
            self._config = self._Config()

        def post(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"path": path, "json": json_data, "auth_preference": auth_preference}

    svc = DocsService(_Client())
    res = svc.append_bullet("doc_tok", "Bullet")

    assert res["json"] == {
        "children": [
            {
                "block_type": 12,
                "bullet": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "Bullet",
                            }
                        }
                    ]
                },
            }
        ]
    }


def test_docs_append_styled_text_uses_text_element_style():
    class _Client:
        class _Config:
            dry_run = True

        def __init__(self):
            self._config = self._Config()

        def post(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"path": path, "json": json_data, "auth_preference": auth_preference}

    svc = DocsService(_Client())
    res = svc.append_styled_text("doc_tok", "Styled", bold=True, italic=True, underline=True)

    assert res["json"] == {
        "children": [
            {
                "block_type": 2,
                "text": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "Styled",
                                "text_element_style": {
                                    "bold": True,
                                    "italic": True,
                                    "underline": True,
                                },
                            }
                        }
                    ]
                },
            }
        ]
    }
    assert res["auth_preference"] == "user"


def test_docs_append_code_block_uses_code_payload():
    class _Client:
        class _Config:
            dry_run = True

        def __init__(self):
            self._config = self._Config()

        def post(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"path": path, "json": json_data, "auth_preference": auth_preference}

    svc = DocsService(_Client())
    res = svc.append_code_block("doc_tok", "print('hi')", language=42, wrap=False, index=1)

    assert res["json"] == {
        "children": [
            {
                "block_type": 14,
                "code": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "print('hi')",
                            }
                        }
                    ],
                    "style": {
                        "language": 42,
                        "wrap": False,
                    },
                },
            }
        ],
        "index": 1,
    }
    assert res["auth_preference"] == "user"


def test_docs_append_rich_text_batches_multiple_block_types():
    class _Client:
        class _Config:
            dry_run = True

        def __init__(self):
            self._config = self._Config()

        def post(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"path": path, "json": json_data, "auth_preference": auth_preference}

    svc = DocsService(_Client())
    res = svc.append_rich_text(
        "doc_tok",
        [
            {"type": "heading", "text": "Title", "level": 2},
            {"type": "text", "text": "Body", "bold": True},
            {"type": "bullet", "text": "Point"},
            {"type": "code", "text": "x = 1", "language": 7, "wrap": False},
        ],
    )

    assert res["json"] == {
        "children": [
            {
                "block_type": 4,
                "heading2": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "Title",
                            }
                        }
                    ]
                },
            },
            {
                "block_type": 2,
                "text": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "Body",
                                "text_element_style": {
                                    "bold": True,
                                    "italic": False,
                                    "underline": False,
                                },
                            }
                        }
                    ]
                },
            },
            {
                "block_type": 12,
                "bullet": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "Point",
                            }
                        }
                    ]
                },
            },
            {
                "block_type": 14,
                "code": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "x = 1",
                            }
                        }
                    ],
                    "style": {
                        "language": 7,
                        "wrap": False,
                    },
                },
            },
        ]
    }
    assert res["auth_preference"] == "user"


def test_docs_append_rich_text_rejects_unsupported_block_type():
    svc = DocsService(_client())

    try:
        svc.append_rich_text("doc_tok", [{"type": "table", "text": "nope"}])
        assert False, "expected ValidationError"
    except ValidationError as exc:
        assert "unsupported rich text block type" in str(exc)


def test_sheets_write_dry_run():
    svc = SheetsService(_client())
    res = svc.write_range("sheet", "A1:B1", [["a", "b"]])
    assert res["dry_run"] is True


def test_sheets_write_uses_resolved_sheet_id_when_not_dry_run():
    class _Cfg:
        dry_run = False

    class _Client:
        def __init__(self):
            self._config = _Cfg()

        def get(self, path: str, params=None, *, auth_preference="auto"):
            if path.endswith("/sheets/query"):
                return {"data": {"sheets": [{"sheet_id": "shtcn123"}]}}
            return {"path": path, "auth_preference": auth_preference}

        def put(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"path": path, "json": json_data, "auth_preference": auth_preference}

    client = _Client()
    svc = SheetsService(client)
    res = svc.write_range("sheet_token", "A1:B1", [["a", "b"]])

    assert res["path"].endswith("/open-apis/sheets/v2/spreadsheets/sheet_token/values")
    assert res["json"] == {
        "valueRange": {
            "range": "shtcn123!A1:B1",
            "values": [["a", "b"]],
        }
    }
    assert res["auth_preference"] == "user"


def test_sheets_read_range_uses_resolved_sheet_id_when_not_dry_run():
    class _Cfg:
        dry_run = False

    class _Client:
        def __init__(self):
            self._config = _Cfg()

        def get(self, path: str, params=None, *, auth_preference="auto"):
            if path.endswith("/sheets/query"):
                return {"data": {"sheets": [{"sheet_id": "shtcn123"}]}}
            return {"path": path, "auth_preference": auth_preference}

    svc = SheetsService(_Client())
    res = svc.read_range("sheet_token", "A1:B1")

    assert res["path"].endswith(
        "/open-apis/sheets/v2/spreadsheets/sheet_token/values/shtcn123%21A1%3AB1"
    )
    assert res["auth_preference"] == "user"


def test_sheets_delete_range_uses_value_ranges_contract():
    class _Cfg:
        dry_run = False

    class _Client:
        def __init__(self):
            self._config = _Cfg()

        def get(self, path: str, params=None, *, auth_preference="auto"):
            if path.endswith("/sheets/query"):
                return {"data": {"sheets": [{"sheet_id": "shtcn123"}]}}
            return {"path": path, "auth_preference": auth_preference}

        def post(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"path": path, "json": json_data, "auth_preference": auth_preference}

    svc = SheetsService(_Client())
    res = svc.delete_range("sheet_token", "A2:B2")

    assert res["path"].endswith("/open-apis/sheets/v2/spreadsheets/sheet_token/values_batch_update")
    assert res["json"] == {
        "valueRanges": [
            {
                "range": "shtcn123!A2:B2",
                "values": [["", ""]],
            }
        ]
    }
    assert res["auth_preference"] == "user"


def test_sheets_delete_single_cell_uses_non_empty_shape():
    class _Cfg:
        dry_run = False

    class _Client:
        def __init__(self):
            self._config = _Cfg()

        def get(self, path: str, params=None, *, auth_preference="auto"):
            if path.endswith("/sheets/query"):
                return {"data": {"sheets": [{"sheet_id": "shtcn123"}]}}
            return {"path": path, "auth_preference": auth_preference}

        def post(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"path": path, "json": json_data, "auth_preference": auth_preference}

    svc = SheetsService(_Client())
    res = svc.delete_range("sheet_token", "C3")

    assert res["json"] == {
        "valueRanges": [
            {
                "range": "shtcn123!C3",
                "values": [[""]],
            }
        ]
    }
    assert res["auth_preference"] == "user"


def test_sheets_resolve_sheet_id_raises_when_missing():
    class _Cfg:
        dry_run = False

    class _Client:
        def __init__(self):
            self._config = _Cfg()

        def get(self, path: str, params=None, *, auth_preference="auto"):
            if path.endswith("/sheets/query"):
                return {"data": {"sheets": []}}
            return {"path": path, "auth_preference": auth_preference}

    svc = SheetsService(_Client())
    try:
        svc.write_range("sheet_token", "A1:B1", [["a", "b"]])
        assert False, "expected ValidationError"
    except ValidationError as exc:
        assert "sheetId not found" in str(exc)


def test_slides_append_dry_run():
    svc = SlidesService(_client())
    res = svc.append_slide("slides", "title")
    assert res["dry_run"] is True


def test_bitable_create_record_dry_run():
    svc = BitableService(_client())
    res = svc.create_record("app", "tbl", {"Name": "Alice"})
    assert res["dry_run"] is True


def test_upload_bytes_dry_run():
    svc = UploadService(_client())
    res = svc.upload_bytes("parent", "a.txt", b"abc", mime="text/plain")
    assert res["dry_run"] is True


def test_drive_service_prefers_user_auth():
    class _Client:
        def get(self, path: str, params=None, *, auth_preference="auto"):
            return {"method": "GET", "auth_preference": auth_preference}

        def post(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"method": "POST", "auth_preference": auth_preference}

        def delete(self, path: str, params=None, json_data=None, *, auth_preference="auto"):
            return {"method": "DELETE", "auth_preference": auth_preference}

    svc = DriveService(_Client())

    assert svc.list_folder("fld")["auth_preference"] == "user"
    assert svc.create_folder("fld", "demo")["auth_preference"] == "user"
    assert svc.read_file_meta("file")["auth_preference"] == "user"
    assert svc.update_file_meta("file", folder_token="folder")["auth_preference"] == "user"
    assert svc.delete_node("file")["auth_preference"] == "user"
    assert svc.move_node("file", "folder")["auth_preference"] == "user"


def test_bitable_service_prefers_user_auth():
    class _Client:
        def get(self, path: str, params=None, *, auth_preference="auto"):
            return {"method": "GET", "auth_preference": auth_preference, "path": path}

        def post(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"method": "POST", "auth_preference": auth_preference}

        def put(self, path: str, json_data=None, *, auth_preference="auto"):
            return {"method": "PUT", "auth_preference": auth_preference}

        def delete(self, path: str, params=None, json_data=None, *, auth_preference="auto"):
            return {"method": "DELETE", "auth_preference": auth_preference}

    svc = BitableService(_Client())

    assert svc.list_tables("app")["auth_preference"] == "user"
    assert svc.list_fields("app", "tbl")["auth_preference"] == "user"
    assert svc.create_table("app", "table")["auth_preference"] == "user"
    assert svc.read_records("app", "tbl")["auth_preference"] == "user"
    assert svc.create_record("app", "tbl", {})["auth_preference"] == "user"
    assert svc.update_record("app", "tbl", "rec", {})["auth_preference"] == "user"
    assert svc.delete_record("app", "tbl", "rec")["auth_preference"] == "user"


def test_upload_service_prefers_user_auth():
    class _Client:
        def post_multipart(self, path: str, data=None, files=None, *, auth_preference="auto"):
            return {"auth_preference": auth_preference, "data": data, "files": files}

    svc = UploadService(_Client())
    res = svc.upload_bytes("parent", "a.txt", b"abc", mime="text/plain")

    assert res["auth_preference"] == "user"


def test_mcp_tools_register_auth_commands():
    tool_specs = {}
    for tool in TOOLS:
        schema = tool["inputSchema"]
        props = list((schema.get("properties") or {}).keys())
        required = list(schema.get("required") or [])
        optional = [name for name in props if name not in required]
        tool_specs[tool["name"]] = {"required": required, "optional": optional}

    assert tool_specs["auth.status"] == {"required": [], "optional": []}
    assert tool_specs["auth.start"] == {"required": [], "optional": ["scope", "mode", "force"]}
    assert tool_specs["auth.poll"] == {
        "required": [],
        "optional": ["device_code", "timeout", "interval", "mode"],
    }
    assert tool_specs["auth.import"] == {
        "required": [],
        "optional": [
            "user_access_token",
            "user_refresh_token",
            "user_token_expires_at",
            "user_refresh_expires_at",
            "user_open_id",
        ],
    }
    assert tool_specs["drive.read"] == {"required": ["file_token"], "optional": []}
    assert tool_specs["drive.update"] == {"required": ["file_token"], "optional": ["name", "folder_token"]}
    assert tool_specs["drive.delete"] == {
        "required": ["file_token"],
        "optional": ["recursive", "request_id"],
    }
    assert tool_specs["drive.move"] == {
        "required": ["file_token", "target_folder_token"],
        "optional": ["request_id"],
    }
    assert tool_specs["upload.bytes"] == {
        "required": ["parent_token", "name", "content"],
        "optional": ["mime"],
    }
    assert tool_specs["docs.read"] == {"required": ["doc_token"], "optional": []}
    assert tool_specs["docs.read_blocks"] == {"required": ["doc_token"], "optional": []}
    assert tool_specs["docs.append_heading"] == {
        "required": ["doc_token", "text"],
        "optional": ["level", "index"],
    }
    assert tool_specs["docs.append_bullet"] == {
        "required": ["doc_token", "text"],
        "optional": ["index"],
    }
    assert tool_specs["docs.append_styled"] == {
        "required": ["doc_token", "text"],
        "optional": ["bold", "italic", "underline", "index"],
    }
    assert tool_specs["docs.append_code"] == {
        "required": ["doc_token", "text"],
        "optional": ["language", "wrap", "index"],
    }
    assert tool_specs["docs.append_rich_text"] == {
        "required": ["doc_token", "blocks"],
        "optional": ["index"],
    }
    assert tool_specs["docs.update"] == {
        "required": ["doc_token", "text"],
        "optional": ["block_id"],
    }
    assert tool_specs["docs.delete"] == {"required": ["doc_token"], "optional": []}
    assert tool_specs["sheets.create"] == {"required": ["title"], "optional": ["folder_token"]}
    assert tool_specs["sheets.read_range"] == {"required": ["sheet_token", "range"], "optional": []}
    assert tool_specs["sheets.append_rows"] == {
        "required": ["sheet_token", "range", "values"],
        "optional": [],
    }
    assert tool_specs["sheets.delete_range"] == {"required": ["sheet_token", "range"], "optional": []}
    assert tool_specs["bitable.list_tables"] == {"required": ["app_token"], "optional": []}
    assert tool_specs["bitable.list_fields"] == {
        "required": ["app_token", "table_id"],
        "optional": [],
    }
    assert tool_specs["bitable.create_table"] == {"required": ["app_token", "name"], "optional": []}
    assert tool_specs["bitable.read_records"] == {
        "required": ["app_token", "table_id"],
        "optional": ["page_token"],
    }
    assert tool_specs["bitable.update_record"] == {
        "required": ["app_token", "table_id", "record_id", "fields"],
        "optional": [],
    }
    assert tool_specs["bitable.delete_record"] == {
        "required": ["app_token", "table_id", "record_id"],
        "optional": [],
    }


def test_http_client_uses_user_bearer_when_auth_mode_user():
    class _Provider:
        def get_user_token(self):
            return "user_token"

        def get_tenant_token(self):
            return "tenant_token"

    cfg = FeishuConfig(
        app_id="app",
        app_secret="secret",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
        auth_mode="user",
        user_refresh_token="refresh",
    )
    client = FeishuHttpClient(cfg, _Provider())
    assert client._get_bearer_token() == "user_token"


def test_http_client_uses_tenant_bearer_when_auth_mode_tenant():
    class _Provider:
        def get_user_token(self):
            return "user_token"

        def get_tenant_token(self):
            return "tenant_token"

    cfg = FeishuConfig(
        app_id="app",
        app_secret="secret",
        base_url="https://open.feishu.cn",
        timeout_seconds=30,
        auth_mode="tenant",
        tenant_access_token="tenant_token",
    )
    client = FeishuHttpClient(cfg, _Provider())
    assert client._get_bearer_token() == "tenant_token"
