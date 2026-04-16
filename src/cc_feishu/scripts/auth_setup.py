#!/usr/bin/env python3
"""
One-click Feishu authorization setup script.

This script automatically:
1. Checks prerequisites (cc-connect config)
2. Configures MCP plugin in ~/.claude/plugins/marketplaces/local/feishu/
3. Configures MCP server in .claude/mcp.json (project-level)
4. Checks authorization status (auto-refresh if needed)
5. Guides through first-time authorization if required

Usage:
    feishu-auth-setup
"""
import json
import os
import sys
import time
from pathlib import Path

# Bilingual messages
MESSAGES = {
    "en": {
        "title": "Feishu Authorization Setup",
        "step": "Step",
        "detect_dir": "Detecting project directory",
        "setup_mcp_plugin": "Setting up MCP plugin (Claude Code)",
        "setup_mcp": "Setting up MCP configuration (project-level)",
        "load_config": "Loading configuration",
        "check_auth": "Checking authorization status",
        "start_auth": "Starting authorization flow",
        "deliver_link": "Authorization link",
        "working_dir": "Working directory",
        "mcp_plugin_written": "MCP plugin written to",
        "mcp_written": "MCP config written to",
        "inherited": "Inherited from cc-connect",
        "already_auth": "Already authorized and token is valid",
        "token_expires": "Token expires",
        "user": "User",
        "open_id": "Open ID",
        "setup_complete": "Setup complete! Authorization is active.",
        "auto_refresh": "Tokens will auto-refresh when needed.",
        "can_use": "You can now use Feishu features in Claude Code conversations.",
        "ask_naturally": "Just ask naturally",
        "example_list": "List my Feishu drive files",
        "example_create": "Create a document called Meeting Notes",
        "example_read": "Read the document at <url>",
        "token_expired": "Access token expired, refreshing",
        "token_refreshed": "Token refreshed successfully",
        "refresh_failed": "Refresh failed",
        "will_retry": "Will start new authorization flow",
        "link_generated": "Authorization link generated",
        "first_time": "First-time setup detected",
        "copy_link": "Please copy the following link and open it in your browser",
        "waiting_auth": "Waiting for authorization",
        "press_ctrl_c": "Press Ctrl+C to cancel",
        "press_enter": "Press Enter after you have authorized in browser",
        "checking_status": "Checking authorization status",
        "auth_failed": "Authorization failed",
        "try_again": "Please try again or check your authorization status.",
        "auth_incomplete": "Authorization incomplete",
        "auth_success": "Authorization successful!",
        "error_missing_config": "Error: Missing app_id or app_secret in cc-connect config.",
        "error_configure": "Please configure cc-connect first",
        "error_start_auth": "Error: Failed to start authorization",
        "error_invalid_resp": "Error: Invalid authorization response from Feishu",
        "error_import": "Error: cc_feishu package not installed.",
        "error_install": "Please run: pip install feishu-docs-drive-supplement",
        "warn_mcp_failed": "MCP config setup failed, but continuing",
        "cancelled": "Cancelled by user.",
    },
    "zh": {
        "title": "飞书授权设置",
        "step": "步骤",
        "detect_dir": "检测项目目录",
        "setup_mcp_plugin": "配置 MCP 插件 (Claude Code)",
        "setup_mcp": "配置 MCP 服务器 (项目级)",
        "load_config": "加载配置",
        "check_auth": "检查授权状态",
        "start_auth": "启动授权流程",
        "deliver_link": "授权链接",
        "working_dir": "工作目录",
        "mcp_plugin_written": "MCP 插件已写入",
        "mcp_written": "MCP 配置已写入",
        "inherited": "已从 cc-connect 继承",
        "already_auth": "已授权且 token 有效",
        "token_expires": "Token 过期时间",
        "user": "用户",
        "open_id": "Open ID",
        "setup_complete": "设置完成！授权已激活。",
        "auto_refresh": "Token 会在需要时自动刷新。",
        "can_use": "现在可以在 Claude Code 对话中使用飞书功能。",
        "ask_naturally": "直接自然提问即可",
        "example_list": "列出我的飞书云盘文件",
        "example_create": "创建一个叫会议记录的文档",
        "example_read": "读取文档 <url>",
        "token_expired": "访问令牌已过期，正在刷新",
        "token_refreshed": "Token 刷新成功",
        "refresh_failed": "刷新失败",
        "will_retry": "将启动新的授权流程",
        "link_generated": "授权链接已生成",
        "first_time": "检测到首次设置",
        "copy_link": "请复制以下链接并在浏览器中打开",
        "waiting_auth": "等待授权",
        "press_ctrl_c": "按 Ctrl+C 取消",
        "press_enter": "在浏览器中授权后按回车",
        "checking_status": "检查授权状态",
        "auth_failed": "授权失败",
        "try_again": "请重试或检查您的授权状态。",
        "auth_incomplete": "授权未完成",
        "auth_success": "授权成功！",
        "error_missing_config": "错误: cc-connect 配置中缺少 app_id 或 app_secret。",
        "error_configure": "请先配置 cc-connect",
        "error_start_auth": "错误: 启动授权失败",
        "error_invalid_resp": "错误: 飞书返回的授权响应无效",
        "error_import": "错误: cc_feishu 包未安装。",
        "error_install": "请运行: pip install feishu-docs-drive-supplement",
        "warn_mcp_failed": "MCP 配置设置失败，但继续执行",
        "cancelled": "用户取消。",
    }
}

# Detect system language
def get_language():
    """Detect system language from environment"""
    lang = os.environ.get('LANG', '').lower()
    if 'zh' in lang or 'cn' in lang:
        return 'zh'
    # Check Windows language
    if sys.platform == 'win32':
        try:
            import locale
            loc = locale.getdefaultlocale()[0]
            if loc and ('zh' in loc.lower() or 'cn' in loc.lower()):
                return 'zh'
        except:
            pass
    return 'en'

LANG = get_language()

def msg(key):
    """Get message in current language"""
    return MESSAGES[LANG].get(key, MESSAGES['en'].get(key, key))

# Try to import required modules
try:
    from cc_feishu.auth.token_provider import FeishuTokenProvider
    from cc_feishu.config import (
        clear_pending_auth_state,
        load_config,
        save_pending_auth_state,
    )
except ImportError as e:
    print(msg("error_import"))
    print(msg("error_install"))
    print(f"Details: {e}")
    sys.exit(1)

# All required scopes for Drive, Docs, Sheets, Bitable
DEFAULT_SCOPES = (
    "drive:drive "
    "drive:drive.readonly "
    "drive:drive.metadata:readonly "
    "drive:file "
    "drive:file:upload "
    "drive:file:download "
    "space:folder:create "
    "space:document:delete "
    "docs:document:read "
    "docs:document:write "
    "docs:document:copy "
    "docs:document.comment:read "
    "docs:document.comment:create "
    "docs:document.comment:update "
    "docs:document.comment:delete "
    "docs:document.media:upload "
    "docs:document.media:download "
    "docx:document "
    "docx:document:create "
    "docx:document:readonly "
    "docx:document:write_only "
    "sheets:spreadsheet "
    "sheets:spreadsheet:create "
    "sheets:spreadsheet:read "
    "sheets:spreadsheet:readonly "
    "bitable:app "
    "bitable:app:readonly "
    "wiki:space:read "
    "wiki:space:retrieve "
    "wiki:space:write_only "
    "wiki:node:read "
    "wiki:node:retrieve "
    "wiki:node:create "
    "wiki:node:copy "
    "wiki:node:update "
    "wiki:wiki:readonly "
    "board:whiteboard:node:read "
    "board:whiteboard:node:create "
    "board:whiteboard:node:delete "
    "docs:permission.member:auth "
    "docs:permission.member:create "
    "docs:permission.member:transfer "
    "docs:event:subscribe "
    "auth:user.id:read "
    "offline_access"
)


def setup_mcp_plugin() -> bool:
    """Setup MCP plugin in Claude Code plugin directory."""
    try:
        plugin_dir = Path.home() / ".claude" / "plugins" / "marketplaces" / "local" / "feishu"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Create .mcp.json
        mcp_config = {
            "feishu": {
                "command": "cc-feishu-mcp",
                "args": []
            }
        }
        mcp_file = plugin_dir / ".mcp.json"
        with open(mcp_file, "w", encoding="utf-8") as f:
            json.dump(mcp_config, f, indent=2, ensure_ascii=False)

        # Create manifest
        manifest_dir = plugin_dir / ".claude-plugin"
        manifest_dir.mkdir(exist_ok=True)

        manifest = {
            "name": "feishu",
            "version": "0.1.0",
            "description": "Feishu Drive, Docs, Sheets, and Bitable operations",
            "author": "Maintainers",
            "homepage": "https://github.com/youshang8520/feishu-docs-drive-supplement",
            "type": "mcp",
            "category": "productivity",
            "tags": ["feishu", "drive", "docs", "sheets", "bitable"],
            "icon": "📄"
        }
        manifest_file = manifest_dir / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"  [ERROR] {msg('warn_mcp_failed')}: {e}")
        return False


def setup_mcp_config(project_dir: Path) -> bool:
    """Setup MCP configuration in .claude/mcp.json"""
    try:
        claude_dir = project_dir / ".claude"
        mcp_file = claude_dir / "mcp.json"

        # Create .claude directory if it doesn't exist
        claude_dir.mkdir(exist_ok=True)

        # Check if mcp.json already exists
        if mcp_file.exists():
            try:
                with open(mcp_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                config = {}
        else:
            config = {}

        # Ensure mcpServers exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Add or update feishu server
        config["mcpServers"]["feishu"] = {
            "command": "cc-feishu-mcp",
            "args": [],
            "env": {},
            "disabled": False
        }

        # Write config
        with open(mcp_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"  [ERROR] {msg('warn_mcp_failed')}: {e}")
        return False


def main():
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except:
            pass

    print("=" * 60)
    print(msg("title"))
    print("=" * 60)
    print()

    # Detect project directory
    project_dir = Path.cwd()
    print(f"[1/6] {msg('detect_dir')}...")
    print(f"  -> {msg('working_dir')}: {project_dir}")

    # Setup MCP plugin (Claude Code)
    print(f"\n[2/6] {msg('setup_mcp_plugin')}...")
    if setup_mcp_plugin():
        plugin_dir = Path.home() / ".claude" / "plugins" / "marketplaces" / "local" / "feishu"
        print(f"  [OK] {msg('mcp_plugin_written')} {plugin_dir}")
    else:
        print(f"  [WARN] {msg('warn_mcp_failed')}")

    # Setup MCP configuration (project-level, optional)
    print(f"\n[3/6] {msg('setup_mcp')}...")
    if setup_mcp_config(project_dir):
        print(f"  [OK] {msg('mcp_written')} {project_dir / '.claude' / 'mcp.json'}")
    else:
        print(f"  [WARN] {msg('warn_mcp_failed')}")

    # Load config
    print(f"\n[4/6] {msg('load_config')}...")
    try:
        config = load_config()
    except Exception as e:
        print(f"{msg('error_missing_config')}")
        print(f"{msg('error_configure')}:")
        print("  ~/.cc-connect/config.toml")
        print(f"Details: {e}")
        sys.exit(1)

    if not config.app_id or not config.app_secret:
        print(msg("error_missing_config"))
        print(f"{msg('error_configure')}:")
        print("  ~/.cc-connect/config.toml")
        sys.exit(1)

    print(f"  [OK] {msg('inherited')}: app_id={config.app_id[:10]}...")

    # Initialize token provider
    provider = FeishuTokenProvider(config)

    # Check if already authorized
    print(f"\n[5/6] {msg('check_auth')}...")
    now = int(time.time())
    has_refresh_token = bool(config.user_refresh_token.strip())
    access_token_valid = bool(config.user_access_token.strip()) and now < config.user_token_expires_at - 60

    if has_refresh_token:
        if access_token_valid:
            print(f"  [OK] {msg('already_auth')}")
            print(f"  [OK] {msg('user')}: {config.user_open_id}")
            print(f"  [OK] {msg('token_expires')}: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(config.user_token_expires_at))}")
            print("\n" + "=" * 60)
            print(msg("setup_complete"))
            print(msg("auto_refresh"))
            print()
            print(msg("can_use"))
            print(f"{msg('ask_naturally')}:")
            print(f"  - '{msg('example_list')}'")
            print(f"  - '{msg('example_create')}'")
            print(f"  - '{msg('example_read')}'")
            print("=" * 60)
            return 0
        else:
            print(f"  -> {msg('token_expired')}...")
            try:
                # Force refresh
                new_token = provider.get_user_token(force_refresh=True)
                print(f"  [OK] {msg('token_refreshed')}")
                print("\n" + "=" * 60)
                print(msg("setup_complete"))
                print()
                print(msg("can_use"))
                print("=" * 60)
                return 0
            except Exception as e:
                print(f"  [ERROR] {msg('refresh_failed')}: {e}")
                print(f"  -> {msg('will_retry')}...")

    # Start device authorization
    print(f"\n[6/6] {msg('start_auth')}...")
    try:
        auth_data = provider.start_device_authorization(DEFAULT_SCOPES)
    except Exception as e:
        print(f"{msg('error_start_auth')}: {e}")
        sys.exit(1)

    device_code = auth_data.get("device_code", "")
    verification_uri_complete = auth_data.get("verification_uri_complete", "")
    interval = auth_data.get("interval", 5)

    if not device_code or not verification_uri_complete:
        print(msg("error_invalid_resp"))
        sys.exit(1)

    # Save pending auth state
    save_pending_auth_state({
        "device_code": device_code,
        "verification_uri_complete": verification_uri_complete,
        "interval": interval,
        "expires_at": int(time.time()) + auth_data.get("expires_in", 900),
    })

    print(f"  [OK] {msg('link_generated')}")

    # Display link for user to open in browser
    print("\n" + "=" * 60)
    print(f"{msg('copy_link')}:")
    print()
    print(f"  {verification_uri_complete}")
    print()
    print("=" * 60)

    # Wait for user to authorize
    print(f"\n{msg('waiting_auth')}...")
    print(f"  ({msg('press_ctrl_c')})")
    input(f"\n  {msg('press_enter')}...")

    # Poll for authorization
    print(f"\n{msg('checking_status')}...")
    try:
        result = provider.poll_device_authorization(
            device_code,
            interval_seconds=interval,
            timeout_seconds=60,
            auth_mode="user"
        )
    except Exception as e:
        print(f"  [ERROR] {msg('auth_failed')}: {e}")
        print(f"\n  {msg('try_again')}")
        sys.exit(1)

    if not result.get("ok"):
        print(f"  [ERROR] {msg('auth_incomplete')}")
        sys.exit(1)

    # Clear pending auth
    clear_pending_auth_state()

    print(f"  [OK] {msg('auth_success')}")
    print(f"  [OK] {msg('user')}: {result.get('user_info', {}).get('name', 'Unknown')}")
    print(f"  [OK] {msg('open_id')}: {result.get('user_open_id', 'Unknown')}")

    # Done
    print(f"\n{msg('setup_complete')}")
    print()
    print("=" * 60)
    print(msg("can_use"))
    print()
    print(f"{msg('ask_naturally')}:")
    print(f"  - '{msg('example_list')}'")
    print(f"  - '{msg('example_create')}'")
    print(f"  - '{msg('example_read')}'")
    print()
    print(msg("auto_refresh"))
    print("=" * 60)
    print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{msg('cancelled')}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


