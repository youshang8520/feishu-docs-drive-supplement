# Feishu 飞书文档与云盘补丁

[English](README.md) | 中文

cc-connect 的飞书补丁包，提供继承配置、CLI 和 MCP 入口、单链接用户授权流程，以及云盘、上传、文档、表格、多维表格的实用操作。

## 这个项目提供什么

- 继承 cc-connect 的飞书应用配置，**无需手动填写配置文件**
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
3. 引导您完成授权
4. 自动保存 token

设置完成后，重启 Claude Code，您就可以在对话中自然使用飞书功能。

## 高级用户

如果需要手动控制，可以直接使用 CLI 命令：

```bash
# 检查授权状态
feishu auth status

# 列出云盘文件
feishu drive list --folder root

# 创建文档
feishu docs create --title "我的文档"

# 追加文本到文档
feishu docs append --doc <文档token> --text "你好"
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

## 文档

- `README.md` — 英文版说明
- `README.feishu.md` — 包概览和命令接口
- `docs/local-claude-import.md` — 工作区集成说明
- `CHANGELOG.md` — 发布历史

## 测试

```bash
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
