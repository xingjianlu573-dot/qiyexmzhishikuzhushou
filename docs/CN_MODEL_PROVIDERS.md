# 国内模型供应商接入指南（CN Model Providers）

> 目标：让企业知识助手在中国大陆网络下全链路使用国产模型，无需特殊网络环境。
> 核心结论：**Dify 平台本身即 AI Provider 抽象层**，支持 40+ 国内外模型供应商；切换模型只需在控制台配置，**无需修改任何代码**。本项目的应用 DSL 中的模型字段为占位，导入后在控制台绑定国内模型即可。

## 1. 推荐组合（国内直连）

| 用途 | 推荐供应商 | 模型示例 |
| --- | --- | --- |
| 对话 LLM | DeepSeek / 阿里云百炼 / 智谱 AI / 月之暗面 | deepseek-chat、qwen-plus、glm-4-flash、moonshot-v1-8k |
| Embedding（向量化） | 阿里云百炼 / 智谱 AI | text-embedding-v3、embedding-3 |
| Rerank（重排，可选） | 阿里云百炼 / 智谱 AI | 以各开放平台模型列表为准（如 bge-reranker 系列托管版） |

> 注意：DeepSeek 与月之暗面目前不提供 Embedding 模型，**Embedding 建议使用通义 text-embedding-v3 或智谱 embedding-3**（RAG 向量化必须配置）。

## 2. 接入步骤（控制台操作，约 5 分钟）

### 2.1 配置模型供应商

1. 登录 Dify 控制台 → 「设置」→「模型供应商」。
2. 点击「添加模型供应商」，按需选择：
   - **DeepSeek**：注册 https://platform.deepseek.com 获取 API Key，填入并保存。
   - **阿里云百炼（通义千问）**：开通阿里云百炼（https://bailian.console.aliyun.com）获取 DashScope API Key。
   - **智谱 AI（BigModel）**：注册 https://open.bigmodel.cn 获取 API Key（glm-4-flash 有免费额度）。
   - **月之暗面 Kimi**：注册 https://platform.moonshot.cn 获取 API Key。
3. 对每个供应商，在供应商详情中选择可用模型（LLM / Embedding / Rerank 分类）并「添加模型」。

### 2.2 在应用工作流中绑定模型

1. 「应用」→ 打开 **Enterprise AI Knowledge Assistant**（导入自 `seed/apps/enterprise-ai-knowledge-assistant.yml`）。
2. 编辑工作流：
   - **LLM 节点（基于知识库回答 / 兜底应答）**：选择已接入的国内 LLM 模型。
   - **企业知识库检索节点**：确认 Embedding 模型（与知识库创建时一致）与 Rerank 模型。
3. 保存并发布。

### 2.3 知识库向量化模型

创建/重建知识库时选择与你检索节点一致的 Embedding 模型。若种子文档已用其他模型索引，可在知识库设置中「重新索引」。

## 3. 环境变量方式（可选）

Dify 支持部分 OpenAI 兼容供应商通过环境变量预设接口地址（见 `.env.example` 第 4 节）。国内模型推荐走控制台配置（界面可视化、多供应商并存、随时切换），本项目的 `.env.example` 已列出各家说明。

## 4. 切换模型不影响功能

- 工作流结构、知识库、引用来源、防幻觉机制与模型无关，切换后功能不变。
- 不同供应商可并存：例如对话用 DeepSeek、Embedding 用通义、Rerank 用智谱。

## 5. 常见问题

| 问题 | 处理 |
| --- | --- |
| 控制台校验模型失败 | 确认 API Key 正确、供应商开放平台已开通对应模型服务（如百炼需开通模型服务） |
| 检索为空 | 检查知识库是否用当前 Embedding 模型完成索引；降低 `score_threshold` 验证 |
| 对话报「模型不存在」 | DSL 导入后模型为占位，需在 LLM 节点重新选择（见 2.2） |
| 想用本地模型 | 可接入 Ollama（内网部署），无需外网；Embedding 可用 bge-m3 等本地模型 |
