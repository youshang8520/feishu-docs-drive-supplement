# Feishu 飞书文档与云盘补丁

[English](README.md) | 中文

面向 Claude Code 的 cc-connect 飞书补丁包，复用 cc-connect 的凭证与配置，提供 CLI 和 MCP 入口、单链接用户授权流程，以及云盘、上传、文档、表格、多维表格的实用操作。

## 这个项目提供什么

- 复用 cc-connect 的飞书应用凭证与配置
- 定位为面向 Claude Code 的 cc-connect 补丁，而不是独立的飞书运行时
- 提供两个入口：
  - `feishu` CLI 命令行工具
  - `cc-feishu-mcp` MCP 服务器
- 支持用户授权（由 `feishu-auth-setup` 自动处理）
- 提供以下功能的实用操作：
  - 云盘 (Drive)
  - 上传 (Upload)
  - 文档 (Docs)
  - 表格 (Sheets)
  - 多维表格 (Bitable)
- 增加了 direct-content 工具，Claude 在用户明确要求读取内容时，可以直接读取文件夹内容、文档正文、表格内容、多维表格记录，减少多余确认

## 安装

```bash
pip install git+https://github.com/youshang8520/feishu-docs-drive-supplement.git
```

## 一键设置

```bash
feishu-auth-setup
```

这将：
1. 为 Claude Code 配置 MCP 插件
2. 设置项目级 MCP 配置
3. 在 `claude` 可用时，将 Feishu MCP 注册到 Claude Code 项目作用域
4. 引导您完成授权
5. 自动保存 token

设置完成后，重启 Claude Code，您就可以在对话中自然使用飞书功能。

**使用示例：**
- "列出我的飞书云盘文件"
- "读取这个文件夹，告诉我里面有什么"
- "读取文档 <url>"
- "读取这个表格：<url>"
- "读取这个多维表格视图：<url>"
- "创建一个叫会议记录的文档"

## 高级用户（CLI 命令）

如果需要通过终端/命令行手动控制，可以直接使用 CLI 命令：

```bash
# 检查授权状态
feishu auth status

# 列出云盘文件
feishu drive list --folder root

# 直接读取文件夹内容
feishu drive read-folder --folder root

# 创建文档
feishu docs create --title "我的文档"

# 直接读取文档正文
feishu docs read-content --doc <文档token>

# 直接读取表格内容
feishu sheets read-content --sheet <sheet_token> --range A1:C10

# 直接读取多维表格内容
feishu bitable read-content --app <app_token> --table <table_id>
```

**注意：** 这些是终端命令，适合开发者和自动化场景。普通用户应该使用 Claude Code 对话方式。

## 功能概览

### 已实现功能

#### 云盘 (Drive)
- 列出文件夹内容
- 直接读取文件夹内容（`read-folder`）
- 创建文件夹
- 读取文件元数据
- 移动文件/文件夹
- 删除节点

#### 上传 (Upload)
- 上传本地文件
- 上传字节内容

#### 文档 (Docs)
- 创建文档
- 读取文档元数据
- 直接读取文档正文（`read-content`）
- 列出文档块
- 追加纯文本
- 追加标题
- 追加列表项
- 追加样式文本
- 追加代码块（`append-code`）
- 批量追加富文本块（`append-rich-text`）
- 删除文档
- 更新指定块的文本（需要提供 `block_id`）

#### 表格 (Sheets)
- 创建电子表格
- 解析工作表 ID
- 读取范围
- 直接读取表格内容（`read-content`）
- 写入范围
- 追加行
- 删除/清空范围

#### 多维表格 (Bitable)
- 列出数据表
- 列出字段
- 创建数据表
- 读取记录
- 直接读取多维表格内容（`read-content`）
- 创建记录
- 更新记录
- 删除记录

#### 授权 (Auth)
- 继承配置
- 单链接授权引导
- 待完成授权复用
- 直接发送授权链接

### 当前限制

- 云盘重命名功能尚未确认为稳定支持的 API 形态
- `docs.update` 在提供 `block_id` 时执行精确块文本更新；不提供时回退到追加行为

## 文档

- `README.md` — 英文版说明
- `README.feishu.md` — 包概览和命令接口
- `docs/feishu-capability-overview.md` — 能力矩阵与定位说明
- `docs/mcp-auto-discovery.md` — Claude Code MCP 注册与校验说明
- `docs/local-claude-import.md` — 工作区集成说明
- `CHANGELOG.md` — 发布历史

## 测试

```bash
pytest
```

## 常见问题

### 1. 这是独立飞书包吗？

不是。它的定位是**面向 Claude Code 的 cc-connect 飞书补丁**，复用 cc-connect 提供的飞书凭证与配置，不是独立的飞书运行时。

### 2. 我需要手动配置飞书应用吗？

通常不需要。如果你已经配置了 cc-connect 的飞书集成，本补丁会自动继承配置。

### 3. MCP 注册需要手动吗？

通常不需要。运行 `feishu-auth-setup` 时，会在 `claude` CLI 可用的情况下自动尝试注册。

如果本机没有 `claude`，不会阻止安装或授权流程，只是会跳过 Claude Code 的 MCP 注册。

### 4. 没有 cc-connect 可以单独使用吗？

不建议按独立产品理解。这个补丁默认依赖 cc-connect 提供飞书应用凭证；如果缺少这部分配置，setup 会明确提示并停止。

### 5. 支持哪些飞书功能？

目前支持云盘、文档、表格、多维表格的常用操作，并提供 direct-content 读取能力。详见上方“功能概览”部分。

### 6. 如何获取文档 token、表格 ID 等参数？

这些参数通常可以从飞书资源的 URL 中获取，或通过相应的列表命令查询。

## 许可证

见 `LICENSE` 文件。

## 贡献

欢迎提交 Issue 和 Pull Request。
