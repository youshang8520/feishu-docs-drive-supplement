# Feishu 飞书文档与云盘补丁

cc-connect 的飞书补丁包，提供继承配置、CLI/MCP/聊天入口、单链接用户授权流程，以及云盘、上传、文档、表格、多维表格的实用操作。

## 这个项目提供什么

- 继承 cc-connect 的飞书应用配置，**无需手动填写配置文件**
- 提供三个入口：
  - `feishu` CLI 命令行工具
  - `cc-feishu-mcp` MCP 服务器
  - `cc-feishu-chat` 固定命令路由器
- 支持用户授权：
  - `auth status` 查看授权状态
  - `auth start` 生成授权链接
  - `auth start
  - `auth poll` 完成授权轮询
  - `auth import` 导入已有授权
- 提供以下功能的实用操作：
  - 云盘 (Drive)
  - 上传 (Upload)
  - 文档 (Docs)
  - 表格 (Sheets)
  - 多维表格 (Bitable)

## 安装

```bash
python -m pip install -e .
```

或者从 GitHub 安装：

```bash
pip install git+https://github.com/你的用户名/feishu-docs-drive-supplement.git
```

## 配置说明

**本补丁默认继承 cc-connect 官方配置，无需额外配置文件。**

配置读取顺序：

1. 环境变量
2. `CC_CONNECT_CONFIG_PATH` 指向的配置文件
3. `~/.cc-connect/config.toml`

期望的配置格式：

```toml
[[projects]]
name = "claudecode"

[[projects.platforms]]
type = "feishu"
[projects.platforms.options]
app_id = "..."
app_secret = "..."
tenant_access_token = "..."
base_url = "https://open.feishu.cn"
```

如果你已经配置了 cc-connect 的飞书集成，本补丁会自动继承这些配置。

## 快速开始

### 1. 检查授权状态

```bash
python -m cc_feishu.cli auth status
```

### 2. 发送授权链接到飞书

```bash
python -m cc_feishu.cli auth start
```

参数说明：

### 3. 完成授权轮询

用户点击授权链接后，运行：

```bash
python -m cc_feishu.cli auth poll --timeout 600
```

### 4. 使用资源操作

授权完成后，可以使用以下命令：

```bash
# 文档操作
python -m cc_feishu.cli docs append --doc <文档token> --text "你好"
python -m cc_feishu.cli docs read-blocks --doc <文档token>
python -m cc_feishu.cli docs update --doc <文档token> --block <块ID> --text "更新的文本"

# 云盘操作
python -m cc_feishu.cli drive list --folder root
python -m cc_feishu.cli drive create-folder --parent <父文件夹token> --name "新文件夹"

# 多维表格操作
python -m cc_feishu.cli bitable list-fields --app <应用token> --table <表格ID>
python -m cc_feishu.cli bitable create-record --app <应用token> --table <表格ID> --fields '{"字段名":"值"}'
```

## 功能概览

### 已实现功能

#### 云盘 (Drive)
- 列出文件夹内容
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
- 列出文档块
- 追加纯文本
- 追加标题
- 追加列表项
- 追加样式文本
- 删除文档
- 更新指定块的文本（需要提供 `block_id`）

#### 表格 (Sheets)
- 创建电子表格
- 解析工作表 ID
- 读取范围
- 写入范围
- 追加行
- 删除/清空范围

#### 多维表格 (Bitable)
- 列出数据表
- 列出字段
- 创建数据表
- 读取记录
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
- 本项目提供固定命令路由器和直接授权链接发送助手，但不是完整的长期运行机器人或 webhook 运行时

## 文档

- `README.md` — 英文版说明
- `README.feishu.md` — 包概览和命令接口
- `docs/feishu-capability-overview.md` — 详细功能矩阵和定位
- `docs/chat-integration-guide.md` — 如何将 `/feishu ...` 风格命令连接到本包
- `docs/local-claude-import.md` — 工作区集成说明
- `CHANGELOG.md` — 发布历史

## 测试

```bash
pytest tests/test_validate.py tests/test_chat_router.py tests/test_mcp_server.py
```

## 常见问题

### 1. 我需要手动配置飞书应用吗？

不需要。如果你已经配置了 cc-connect 的飞书集成，本补丁会自动继承配置。

### 2. 授权链接可以发送到飞书吗？

可以。使用 `auth start

### 3. 支持哪些飞书功能？

目前支持云盘、文档、表格、多维表格的常用操作。详见上方"功能概览"部分。

### 4. 如何获取文档 token、表格 ID 等参数？

这些参数通常可以从飞书资源的 URL 中获取，或通过相应的列表命令查询。

## 许可证

见 `LICENSE` 文件。

## 贡献

欢迎提交 Issue 和 Pull Request。
