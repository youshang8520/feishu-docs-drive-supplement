TOOLS = {
    "auth.status": {
        "required": [],
        "optional": [],
    },
    "auth.start": {
        "required": [],
        "optional": ["mode", "scope", "force"],
    },
    "auth.send_link": {
        "required": ["receive_id"],
        "optional": ["receive_id_type", "text", "force", "mode", "scope"],
    },
    "auth.poll": {
        "required": ["device_code"],
        "optional": ["interval", "timeout", "mode"],
    },
    "auth.import": {
        "required": [],
        "optional": [
            "mode",
            "access_token",
            "refresh_token",
            "expires_at",
            "refresh_expires_at",
            "open_id",
        ],
    },
    "drive.list": {
        "required": ["folder_token"],
        "optional": ["page_token"],
    },
    "drive.create_folder": {
        "required": ["parent_token", "name"],
        "optional": ["request_id"],
    },
    "drive.read": {
        "required": ["file_token"],
        "optional": [],
    },
    "drive.update": {
        "required": ["file_token"],
        "optional": ["name", "folder_token"],
    },
    "drive.delete": {
        "required": ["token"],
        "optional": ["recursive", "request_id", "node_type"],
    },
    "drive.move": {
        "required": ["token", "target_folder_token"],
        "optional": ["request_id"],
    },
    "upload.bytes": {
        "required": ["parent_token", "name", "content"],
        "optional": ["mime"],
    },
    "docs.create": {
        "required": ["title"],
        "optional": ["folder_token"],
    },
    "docs.read": {
        "required": ["doc_token"],
        "optional": [],
    },
    "docs.read_blocks": {
        "required": ["doc_token"],
        "optional": [],
    },
    "docs.append": {
        "required": ["doc_token", "text"],
        "optional": [],
    },
    "docs.append_heading": {
        "required": ["doc_token", "text"],
        "optional": ["level", "index"],
    },
    "docs.append_bullet": {
        "required": ["doc_token", "text"],
        "optional": ["index"],
    },
    "docs.append_styled": {
        "required": ["doc_token", "text"],
        "optional": ["bold", "italic", "underline", "index"],
    },
    "docs.update": {
        "required": ["doc_token", "text"],
        "optional": ["block_id"],
    },
    "docs.delete": {
        "required": ["doc_token"],
        "optional": [],
    },
    "sheets.create": {
        "required": ["title"],
        "optional": ["folder_token"],
    },
    "sheets.read_range": {
        "required": ["sheet_token", "range"],
        "optional": [],
    },
    "sheets.write": {
        "required": ["sheet_token", "range", "values"],
        "optional": [],
    },
    "sheets.append_rows": {
        "required": ["sheet_token", "range", "values"],
        "optional": [],
    },
    "sheets.delete_range": {
        "required": ["sheet_token", "range"],
        "optional": [],
    },
    "slides.append": {
        "required": ["slides_token", "title"],
        "optional": [],
    },
    "bitable.list_tables": {
        "required": ["app_token"],
        "optional": [],
    },
    "bitable.list_fields": {
        "required": ["app_token", "table_id"],
        "optional": [],
    },
    "bitable.create_table": {
        "required": ["app_token", "name"],
        "optional": [],
    },
    "bitable.read_records": {
        "required": ["app_token", "table_id"],
        "optional": ["view_id"],
    },
    "bitable.create_record": {
        "required": ["app_token", "table_id", "fields"],
        "optional": [],
    },
    "bitable.update_record": {
        "required": ["app_token", "table_id", "record_id", "fields"],
        "optional": [],
    },
    "bitable.delete_record": {
        "required": ["app_token", "table_id", "record_id"],
        "optional": [],
    },
}
