"""MCP tool definitions for Feishu integration."""

TOOLS = [
    {
        "name": "auth.status",
        "description": "Check Feishu authorization status",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "auth.start",
        "description": "Start Feishu device authorization flow",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "description": "OAuth scope"},
                "mode": {"type": "string", "description": "Auth mode (user/tenant)"},
                "force": {"type": "boolean", "description": "Force new authorization"},
            },
        },
    },
    {
        "name": "auth.poll",
        "description": "Poll for authorization completion",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device_code": {"type": "string", "description": "Device code"},
                "timeout": {"type": "integer", "description": "Timeout in seconds"},
                "interval": {"type": "integer", "description": "Poll interval"},
                "mode": {"type": "string", "description": "Auth mode"},
            },
        },
    },
    {
        "name": "auth.import",
        "description": "Import existing user tokens",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_access_token": {"type": "string"},
                "user_refresh_token": {"type": "string"},
                "user_token_expires_at": {"type": "integer"},
                "user_refresh_expires_at": {"type": "integer"},
                "user_open_id": {"type": "string"},
            },
        },
    },
    {
        "name": "drive.list",
        "description": "List files in a Feishu Drive folder",
        "inputSchema": {
            "type": "object",
            "properties": {
                "folder_token": {"type": "string", "description": "Folder token (use 'root' for root)"},
                "page_token": {"type": "string", "description": "Pagination token"},
            },
        },
    },
    {
        "name": "drive.create_folder",
        "description": "Create a folder in Feishu Drive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parent_token": {"type": "string", "description": "Parent folder token"},
                "name": {"type": "string", "description": "Folder name"},
                "request_id": {"type": "string", "description": "Idempotency key"},
            },
            "required": ["parent_token", "name"],
        },
    },
    {
        "name": "drive.read",
        "description": "Read file metadata from Feishu Drive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_token": {"type": "string", "description": "File token"},
            },
            "required": ["file_token"],
        },
    },
    {
        "name": "drive.update",
        "description": "Update file metadata in Feishu Drive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_token": {"type": "string", "description": "File token"},
                "name": {"type": "string", "description": "New name"},
                "folder_token": {"type": "string", "description": "Target folder token"},
            },
            "required": ["file_token"],
        },
    },
    {
        "name": "drive.move",
        "description": "Move file/folder in Feishu Drive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_token": {"type": "string", "description": "File/folder token"},
                "target_folder_token": {"type": "string", "description": "Target folder token"},
                "request_id": {"type": "string", "description": "Idempotency key"},
            },
            "required": ["file_token", "target_folder_token"],
        },
    },
    {
        "name": "drive.delete",
        "description": "Delete file/folder from Feishu Drive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_token": {"type": "string", "description": "File/folder token"},
                "recursive": {"type": "boolean", "description": "Delete recursively"},
                "request_id": {"type": "string", "description": "Idempotency key"},
            },
            "required": ["file_token"],
        },
    },
    {
        "name": "upload.bytes",
        "description": "Upload file content to Feishu Drive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parent_token": {"type": "string", "description": "Parent folder token"},
                "name": {"type": "string", "description": "File name"},
                "content": {"type": "string", "description": "File content"},
                "mime": {"type": "string", "description": "MIME type"},
            },
            "required": ["parent_token", "name", "content"],
        },
    },
    {
        "name": "docs.create",
        "description": "Create a Feishu document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "folder_token": {"type": "string", "description": "Parent folder token"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "docs.read",
        "description": "Read Feishu document metadata",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_token": {"type": "string", "description": "Document token"},
            },
            "required": ["doc_token"],
        },
    },
    {
        "name": "docs.read_blocks",
        "description": "List all blocks in a Feishu document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_token": {"type": "string", "description": "Document token"},
            },
            "required": ["doc_token"],
        },
    },
    {
        "name": "docs.append",
        "description": "Append text to a Feishu document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_token": {"type": "string", "description": "Document token"},
                "text": {"type": "string", "description": "Text to append"},
            },
            "required": ["doc_token", "text"],
        },
    },
    {
        "name": "docs.append_heading",
        "description": "Append heading to a Feishu document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_token": {"type": "string", "description": "Document token"},
                "text": {"type": "string", "description": "Heading text"},
                "level": {"type": "integer", "description": "Heading level (1-9)"},
                "index": {"type": "integer", "description": "Insert position"},
            },
            "required": ["doc_token", "text"],
        },
    },
    {
        "name": "docs.append_bullet",
        "description": "Append bullet list item to a Feishu document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_token": {"type": "string", "description": "Document token"},
                "text": {"type": "string", "description": "Bullet text"},
                "index": {"type": "integer", "description": "Insert position"},
            },
            "required": ["doc_token", "text"],
        },
    },
    {
        "name": "docs.append_styled",
        "description": "Append styled text to a Feishu document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_token": {"type": "string", "description": "Document token"},
                "text": {"type": "string", "description": "Text content"},
                "bold": {"type": "boolean", "description": "Bold style"},
                "italic": {"type": "boolean", "description": "Italic style"},
                "underline": {"type": "boolean", "description": "Underline style"},
                "index": {"type": "integer", "description": "Insert position"},
            },
            "required": ["doc_token", "text"],
        },
    },
    {
        "name": "docs.update",
        "description": "Update block text in a Feishu document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_token": {"type": "string", "description": "Document token"},
                "text": {"type": "string", "description": "New text"},
                "block_id": {"type": "string", "description": "Block ID to update"},
            },
            "required": ["doc_token", "text"],
        },
    },
    {
        "name": "docs.delete",
        "description": "Delete a Feishu document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_token": {"type": "string", "description": "Document token"},
            },
            "required": ["doc_token"],
        },
    },
    {
        "name": "sheets.create",
        "description": "Create a Feishu spreadsheet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Spreadsheet title"},
                "folder_token": {"type": "string", "description": "Parent folder token"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "sheets.read_range",
        "description": "Read cell range from a Feishu spreadsheet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sheet_token": {"type": "string", "description": "Spreadsheet token"},
                "range": {"type": "string", "description": "Cell range (e.g., A1:B10)"},
            },
            "required": ["sheet_token", "range"],
        },
    },
    {
        "name": "sheets.write",
        "description": "Write to cell range in a Feishu spreadsheet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sheet_token": {"type": "string", "description": "Spreadsheet token"},
                "range": {"type": "string", "description": "Cell range"},
                "values": {"type": "array", "description": "2D array of values"},
            },
            "required": ["sheet_token", "range", "values"],
        },
    },
    {
        "name": "sheets.append_rows",
        "description": "Append rows to a Feishu spreadsheet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sheet_token": {"type": "string", "description": "Spreadsheet token"},
                "range": {"type": "string", "description": "Target range"},
                "values": {"type": "array", "description": "2D array of values"},
            },
            "required": ["sheet_token", "range", "values"],
        },
    },
    {
        "name": "sheets.delete_range",
        "description": "Delete/clear cell range in a Feishu spreadsheet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sheet_token": {"type": "string", "description": "Spreadsheet token"},
                "range": {"type": "string", "description": "Cell range"},
            },
            "required": ["sheet_token", "range"],
        },
    },
    {
        "name": "bitable.list_tables",
        "description": "List tables in a Feishu bitable",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Bitable app token"},
            },
            "required": ["app_token"],
        },
    },
    {
        "name": "bitable.list_fields",
        "description": "List fields in a bitable table",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Bitable app token"},
                "table_id": {"type": "string", "description": "Table ID"},
            },
            "required": ["app_token", "table_id"],
        },
    },
    {
        "name": "bitable.create_table",
        "description": "Create a table in a Feishu bitable",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Bitable app token"},
                "name": {"type": "string", "description": "Table name"},
            },
            "required": ["app_token", "name"],
        },
    },
    {
        "name": "bitable.read_records",
        "description": "Read records from a bitable table",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Bitable app token"},
                "table_id": {"type": "string", "description": "Table ID"},
                "page_token": {"type": "string", "description": "Pagination token"},
            },
            "required": ["app_token", "table_id"],
        },
    },
    {
        "name": "bitable.create_record",
        "description": "Create a record in a bitable table",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Bitable app token"},
                "table_id": {"type": "string", "description": "Table ID"},
                "fields": {"type": "object", "description": "Record fields"},
            },
            "required": ["app_token", "table_id", "fields"],
        },
    },
    {
        "name": "bitable.update_record",
        "description": "Update a record in a bitable table",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Bitable app token"},
                "table_id": {"type": "string", "description": "Table ID"},
                "record_id": {"type": "string", "description": "Record ID"},
                "fields": {"type": "object", "description": "Updated fields"},
            },
            "required": ["app_token", "table_id", "record_id", "fields"],
        },
    },
    {
        "name": "bitable.delete_record",
        "description": "Delete a record from a bitable table",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "Bitable app token"},
                "table_id": {"type": "string", "description": "Table ID"},
                "record_id": {"type": "string", "description": "Record ID"},
            },
            "required": ["app_token", "table_id", "record_id"],
        },
    },
]
