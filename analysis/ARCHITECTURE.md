# Dify 架构分析（Enterprise AI Knowledge Assistant 项目基线）

> 分析对象：langgenius/dify `main` 分支（`api/pyproject.toml` 版本 **1.17.1**）
> 分析方式：基于上游源码关键文件实读（快照见 `dify-src/`，文件树见 `dify-file-tree.txt`）
> 更新时间：2026-10-05

## 1. 总体形态

Dify 是一个 **LLM 应用开发平台**（monorepo），一次部署即可获得：可视化工作流编排、RAG 知识库流水线、Agent、模型管理、LLMOps 观测与全量开放 API。仓库顶层结构（共 17,510 个文件）：

| 目录 | 规模 | 职责 |
| --- | --- | --- |
| `web/` | 7,815 | Next.js（App Router）+ React + TypeScript 前端，含控制台与分享页（`web/app/(shareLayout)/chat/[token]/page.tsx`） |
| `api/` | 4,248 | Python 3.12 后端（Flask + Celery），含 RAG 引擎、工作流引擎、API 层、模型层 |
| `packages/` | 980 | 前端共享包（`dify-ui`、`contracts`、`iconify-collections` 等） |
| `dify-agent/` `cli/` `e2e/` | 584 | Agent 运行时 / CLI 工具 / 端到端测试 |
| `docker/` | 83 | Docker Compose 部署（`docker-compose.yaml` 定义 13+ 服务） |
| `sdks/` | 49 | 多语言 SDK |
| `docs/` `scripts/` | 77 | 文档与工程脚本 |

## 2. 技术栈（源码核实）

**后端**（`api/pyproject.toml`）：
- Python `~=3.12.0`；API 框架 Flask 3.x + flask-restx；异步任务 Celery 5.x；队列/缓存 Redis；主库 PostgreSQL（psycopg2）；HTTP 服务 gunicorn + gevent + gevent-websocket（Socket.IO 流式）。
- 可观测：OpenTelemetry（Flask/Celery/Redis/httpx/SQLAlchemy 全链路插桩）。
- 工作流运行时：`graphon==0.7.0`（新图执行引擎）；向量库与观测均以 workspace provider 包形式注入（`api/providers/vdb/vdb-*`、`api/providers/trace/*`）。

**前端**（`web/package.json`）：Next.js（App Router）+ React + TypeScript；状态管理 jotai + TanStack Query；i18next 多语言（`web/i18n/` 1,401 个文件）；图表 ECharts。

**部署**（`docker/docker-compose.yaml`）：api / api_websocket / worker / worker_beat / web / db_postgres / db_mysql / redis / sandbox / local_sandbox / plugin_daemon / agent_backend / ssrf_proxy / nginx / certbot / weaviate（默认向量库，另有 Qdrant、pgvector、Milvus 等 30+ 向量库可切换，见 `api/configs/middleware/vdb/*`）。

## 3. 核心模块

### 3.1 RAG 知识库引擎 `api/core/rag/`

- **文档解析**：`core/rag/extractor/`（unstructured / firecrawl / watercrawl 等抽取器）。
- **清洗与后处理**：`core/rag/cleaner/`、`core/rag/data_post_processor/`（含 reorder 重排）。
- **索引**：`core/rag/index_processor/index_processor_base.py`（Embedding + 写入向量库）。
- **关键词检索**：`core/rag/datasource/keyword/`（jieba 分词，中文场景）。
- **向量检索**：`core/rag/datasource/vdb/` + 各 `vdb-*` provider 包（Qdrant 实现见 `dify-src/api__providers__vdb__vdb-qdrant__src__dify_vdb_qdrant__qdrant_vector.py`）。
- **检索服务**（直接支撑"引用来源 + 防幻觉"）：`core/rag/datasource/retrieval_service.py`
  - 检索模式：关键词 / 向量 / 混合检索（`RetrievalMethod`）。
  - 质量参数：`top_k`（默认 4）、`score_threshold`（相似度阈值过滤）、`reranking_enable + reranking_model`（重排模型二次排序）、检索结果去重（`_deduplicate_documents`）。
  - 检索结果携带 `score` 与元数据，即引用来源的数据基础。

### 3.2 工作流引擎 `api/core/workflow/`

- `node_factory.py` 节点注册与实例化；`graph_topology.py` 图拓扑；`node_runtime.py` 执行。
- 内置节点（`graphon/enums.py BuiltinNodeTypes` 核实）：`start / llm / answer / knowledge-retrieval / if-else / code / agent / question-classifier / http-request / iteration / loop / variable-aggregator` 等。
- 工作流节点类型字符串（DSL 中 `type` 字段）：`start`、`llm`、`answer`、`knowledge-retrieval`、`if-else` 等（与 DSL 校验脚本使用的枚举一致）。

### 3.3 应用与应用 API

- 应用运行时：`api/core/app/apps/chat/app_runner.py`（高级对话模式）。
- DSL 导入/导出：`api/services/app_dsl_service.py`（支持 yaml-content / yaml-url 导入、版本兼容检查、依赖提取）。
- 控制台 API：`api/controllers/console/`（知识库管理见 `datasets/datasets.py`、命中测试见 `datasets/hit_testing.py`）。
- 服务 API：`api/controllers/service_api/`（对外接口，知识库 `datasets/dataset.py`：创建/列表/上传文档/标签等）。

### 3.4 知识库数据模型 `api/models/dataset.py`

Dataset（数据集）/ Document（文档）/ Segment（分段）模型，支撑"知识库管理"：创建、上传、分段、索引状态、命中测试、标签。

### 3.5 引用来源（产品能力）

- DSL 特性 `workflow.features.retriever_resource.enabled=true`：聊天界面自动渲染检索引用卡片（本项目的"引用来源"落地于此）。

## 4. 可复用部分（本项目改造策略 = 最大化复用）

| 能力 | 复用方式 | 说明 |
| --- | --- | --- |
| 平台本体（api + web + docker） | 原样部署，零重构 | Docker 镜像直接运行，无需改动上游代码 |
| RAG 检索质量机制 | 通过 DSL 配置启用 | `score_threshold` + `reranking` + `top_k` 即"减少幻觉"的工程基础 |
| 知识库管理全链路 | 复用控制台 + 服务 API | 本项目提供 `deploy/scripts/seed-kb.py` 一键建库导文档 |
| 工作流自动处理 | 复用工作流引擎 | 本项目 DSL 用 `knowledge-retrieval → if-else → llm/兜底` 实现"命中回答/未命中转人工" |
| 引用来源 | 复用 `retriever_resource` 特性 | DSL 已启用，前端原生渲染引用卡片 |
| 对话历史 | 复用 LLM 节点记忆窗口 | DSL 配置 `memory.window.enabled=true, size=10` |

## 5. 改造边界（不改什么）

- 不修改上游 `api/`、`web/`、`packages/` 源码（许可证约束：保留 Dify 标识，见 LICENSE）。
- 所有"改造"落在**配置（DSL / env）+ 数据（知识库种子）+ 文档**三层，可完整回滚、可跟随上游升级。
