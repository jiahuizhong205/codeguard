# CodeGuard

一个以治理为核心的 Coding Agent Harness —— 从零实现，不依赖 LangChain、AutoGen 等现成框架，纯 Python 构建。

## CodeGuard 是什么？

CodeGuard 是一个 Coding Agent Harness，实现了完整的 agent 主循环（组织上下文 → 调用 LLM → 解析动作 → 护栏检查 → 工具执行 → 反馈回灌 → 停机判断），并深入聚焦**治理**维度：护栏引擎、HITL 状态机、范围围栏和审计日志。

每个核心机制都是确定性代码，可用 mock LLM 进行单元测试 —— 没有任何"用提示词假装安全机制"的设计。

## 快速开始

### 方式一：交互式初始化（推荐）

```bash
git clone https://github.com/jiahuizhong205/codeguard.git
cd codeguard
pip install -e ".[dev]"
codeguard init          # 交互式引导，生成 .env
codeguard serve         # 启动服务
```

在浏览器中打开 http://localhost:8000。

### 方式二：手动编辑 .env

```bash
cp .env.example .env    # 复制配置模板
# 编辑 .env，填入你的 API 地址、Key、模型名
codeguard serve
```

### Docker 运行

```bash
docker pull ghcr.io/jiahuizhong205/codeguard:latest

# 首次运行：交互式配置
docker run -it -p 8000:8000 -v codeguard-data:/data codeguard:latest init

# 启动服务
docker run -p 8000:8000 -v codeguard-data:/data -v /path/to/workspace:/workspace codeguard:latest serve
```

## LLM API 配置

所有 LLM 相关配置集中在 **一个文件** `.env` 中，修改后重启服务即可生效。

### 配置项

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `LLM_BASE_URL` | LLM API 地址（OpenAI 兼容格式） | `https://api.example.com` |
| `LLM_API_KEY` | API Key | `sk-xxxxxxxxxxxx` |
| `LLM_MODEL` | 模型名称 | `gpt-4` |

### 修改方法

1. 编辑项目根目录的 `.env` 文件
2. 修改对应的值
3. 重启服务：`codeguard serve`

`.env` 文件示例：
```env
LLM_BASE_URL=https://your-api-url.example.com
LLM_API_KEY=sk-your-api-key
LLM_MODEL=gpt-4
```

> **安全说明**：`.env` 已在 `.gitignore` 中排除，不会被提交到 Git。API Key 不会出现在日志或终端输出中。查看配置状态运行 `codeguard credentials`，只显示是否已配置和 URL，不回显 Key。

## 机制演示

```bash
codeguard demo
```

在 mock LLM 下确定性复现 3 个治理行为：
1. 护栏拦截 `rm -rf` 危险命令
2. 反馈闭环驱动 agent 自我修正
3. 范围围栏拦截 workspace 路径逃逸

## 测试

```bash
make test
```

所有核心机制均有基于 mock LLM 的确定性单元测试。

## 架构

```
Agent 主循环
├── LLM 客户端（可注入 mock）
├── 工具分发器
│   ├── 内置工具（文件读写、Shell、测试、Lint）
│   └── MCP 工具适配器（外部工具服务）
├── 护栏引擎（11 条内置规则，可 YAML 扩展）
├── HITL 管理器（审批状态机）
├── 范围围栏（workspace 边界 enforcement）
├── 审计日志（JSONL 格式，参数脱敏）
├── 反馈验证器（测试、Lint）
├── 记忆存储（跨会话 JSON）
└── 技能加载器（Markdown 技能文件）
```

## 技术栈

- Python 3.12、FastAPI、pytest
- React + Vite（前端）
- Docker（分发）
- cryptography/Fernet（凭据加密）

## 已知限制

- 需要 Docker（或从源码运行需 Python 3.12+）
- workspace 需挂载到容器内
- MCP 服务器需在容器内可访问
- Docker 内无系统钥匙串（使用加密文件方案）

## 许可证

MIT
