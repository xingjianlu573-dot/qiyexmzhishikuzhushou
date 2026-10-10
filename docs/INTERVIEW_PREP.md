# Enterprise AI Knowledge Assistant · 面试知识点手册

> 用途：3 小时内掌握本项目并应对 AI 应用实施工程师面试。全部内容基于仓库真实文件（README / analysis / docs / seed / deploy / scripts），可到对应路径溯源。

---

## 0. 学习地图（3 小时版）

| 时段 | 内容 | 对应章节 |
| --- | --- | --- |
| 0:00-0:30 | 项目定位、业务痛点、解决方案 | 1-3 |
| 0:30-1:00 | 技术架构、RAG 原理、核心功能 | 4-5 |
| 1:00-1:30 | 工作流 DSL、防幻觉三层机制 | 6-8 |
| 1:30-2:00 | 数据层、校验测试、部署、国产化 | 9-13 |
| 2:00-2:30 | 演示体验站 + 高频面试问答 | 14-15 |
| 2:30-3:00 | 做练习题，查漏补缺 | 16 |

---

## 1. 一句话定位（面试开场白）

> 「这是一个基于开源 LLM 应用平台 Dify 改造的企业级 AI 知识助手。企业员工和客服通过自然语言查询产品说明书、技术文档、IT 运维 SOP、售后流程和 FAQ；AI 回答基于企业知识库生成、强制带引用来源，检索不到依据时自动转人工，从机制上减少幻觉。支持国产大模型接入和中国大陆网络环境部署。」

## 2. 项目背景与企业痛点

**背景**：企业沉淀大量文档，但分散在网盘、Wiki、邮件和老员工经验里；员工检索成本高、回答口径不一、高频问题重复消耗人力。

**四大痛点**（面试常问"为什么要做这个项目"）：

| 痛点 | 具体表现 |
| --- | --- |
| 知识分散 | 文档散落多处，检索一次平均 15-30 分钟 |
| 口径不一 | 同一问题不同人回答不一致，SOP 更新后旧内容仍被引用 |
| 依赖人工 | 高频问题占一线人力 40% 以上，重复回答 |
| 幻觉风险 | 通用大模型直接问答会编造，必须基于知识库 + 引用溯源 |

## 3. 解决方案（总流程 + 防幻觉）

```
用户提问 → 企业知识库检索(RAG: 5 数据集 × 多路检索, 分数阈值 0.5, 重排)
        → 检索结果判断(if-else: result not empty)
             ├─ 命中 → LLM 基于知识库回答（防幻觉提示词 + 引用标注）→ 回答(引用卡片)
             └─ 未命中 → 兜底应答（告知未命中 + 转 IT 服务台/工单）
```

**防幻觉三层机制**（面试核心亮点）：
1. 检索侧：分数阈值过滤（score_threshold）+ 重排（reranking）+ top_k 控制
2. 提示词侧：仅依据上下文、无依据明说、强制引用标注
3. 路由侧：无依据不硬答，走兜底转人工

## 4. 技术架构

**改造方式（作品集项目的定位）**：配置 + 数据 + 文档层改造，最大化复用上游，不重构上游代码。上游 100% 复用，新增代码仅 2 个校验脚本 + 1 个导入脚本（约 400 行）。

**六层架构**：

| 层 | 技术 | 说明 |
| --- | --- | --- |
| 平台本体（上游零改造） | Dify 1.17.1 | Next.js 前端 + Flask 后端 + Celery 异步 + PostgreSQL + Redis + Weaviate 向量库 |
| RAG 引擎（复用上游） | `api/core/rag` | 文档抽取→清洗→向量化→检索（关键词/向量/混合）→重排 |
| 应用层（本项目） | 高级对话 DSL | knowledge-retrieval → if-else → LLM/兜底 |
| 数据层（本项目） | 12 篇文档、5 分类 | `seed/knowledge-base/` |
| 部署层（本项目） | Docker Compose + 导入脚本 | `deploy/` |
| 质量层（本项目） | 校验脚本 | validate_dsl 30 PASS / validate_seed 48 PASS |

**Dify 平台技术栈（面试可能被问）**：
- 后端：Python 3.12 + Flask 3.x + flask-restx；Celery 异步任务；Redis 缓存/队列；PostgreSQL 主库；gunicorn + gevent 部署；OpenTelemetry 可观测；graphon 0.7.0 图执行引擎
- 前端：Next.js（App Router）+ React + TypeScript；jotai + TanStack Query；i18next 多语言
- 部署：docker-compose 13+ 服务（api / worker / web / db / redis / sandbox / nginx / weaviate 等），支持 30+ 向量库切换

**核心模块（上游源码分析结论）**：
- RAG 引擎 `api/core/rag/`：抽取器（unstructured 等）、清洗、索引（Embedding+写向量库）、关键词检索（jieba 分词，中文）、向量检索（vdb provider）、检索服务 `retrieval_service.py`（top_k 默认 4、score_threshold、reranking、去重；结果带 score 与元数据 = 引用来源的数据基础）
- 工作流引擎 `api/core/workflow/`：node_factory / graph_topology / node_runtime；内置节点 start/llm/answer/knowledge-retrieval/if-else/code/agent 等
- 应用与 API：app_runner（高级对话）、DSL 导入导出 app_dsl_service、控制台 API（知识库/命中测试）、服务 API（创建/上传文档）
- 数据模型 `api/models/dataset.py`：Dataset/Document/Segment
- 引用来源：DSL 特性 `workflow.features.retriever_resource.enabled=true` → 前端渲染引用卡片

## 5. 核心功能（6 项，面试逐条能说）

1. **文档上传 / 知识库管理**：支持 PDF / Word / Markdown；5 个数据集按分类管理，命中测试验证检索质量
2. **RAG 检索**：多路检索 + 分数阈值 0.5 + 重排；中英文混合场景关键词（jieba）兜底
3. **AI 问答**：高级对话应用，10 轮对话记忆，回答仅依据检索上下文
4. **引用来源**：聊天界面渲染引用卡片，回答末尾标注「引用：[文档名]」
5. **对话历史**：Web App 会话管理 + LLM 节点记忆窗口（memory.window size=10）
6. **工作流自动处理问题**：命中回答 / 未命中转人工，一次配置全自动路由

## 6. 工作流 DSL 详解（面试重点，能画出节点图）

文件：`seed/apps/enterprise-ai-knowledge-assistant.yml`（mode: advanced-chat，version 0.3.1）

**7 个节点**：
1. `start`（开始）：入口，sys.query 用户问题
2. `knowledge_retrieval`（企业知识库检索）：dataset_ids 绑定 5 个数据集；`retrieval_mode: multiple` 多路检索；`top_k: 5`、`score_threshold: 0.5`、`reranking_enable: true`
3. `route`（检索结果判断 if-else）：条件 = `knowledge_retrieval.result not empty`，逻辑 and
4. `llm_answer`（基于知识库回答）：context 绑定检索结果；temperature 0.2；system 提示词五条铁律（只依据上下文/无依据明说/强制引用标注/不相关提示换问法/简洁结构化）
5. `answer`（回答）：输出 `{{#llm_answer.text#}}`
6. `llm_fallback`（兜底应答）：temperature 0.3；提示词规定告知"未检索到资料→转 IT 服务台 4008 转 100/工单→给 1-2 条示例问法→不编造"
7. `answer_fallback`（兜底回答）：输出 `{{#llm_fallback.text#}}`

**连线**：start→knowledge_retrieval→route→(true)llm_answer→answer；(false)llm_fallback→answer_fallback

**DSL 其他特性**：opening_statement（开场白）、suggested_questions（6 个建议问题）、suggested_questions_after_answer、retriever_resource.enabled: true（引用卡片）

## 7. RAG 原理与检索质量参数（面试核心，必须讲清）

RAG = 检索增强生成（Retrieval-Augmented Generation）：先检索知识库相关内容，再让 LLM 基于检索结果回答，解决"LLM 不知道企业私有知识 + 会幻觉"两个问题。

本项目知识库流水线：**文档解析 → 清洗 → 向量化（Embedding）→ 写入向量库 → 检索 → 重排 → LLM 生成**。

三个关键质量参数（要能解释含义和面试表达）：
- `top_k`（本项目 5）：取回多少候选片段。太小漏信息，太大上下文噪声多
- `score_threshold`（本项目 0.5）：低于相似度阈值的片段直接丢弃，过滤低相关
- `reranking`（本项目开启）：粗检索后用重排模型二次排序，把最相关的排前面（可选模型如 bge-reranker 系列）

**多路检索（multiple）**：同时走关键词检索（jieba 分词，中文/精确词兜底）+ 向量检索（语义相似），再合并去重。中英文混合场景下关键词兜底很重要。

**Embedding 注意点**（面试可能追问）：向量化必须配置 Embedding 模型；DeepSeek 和月之暗面不提供 Embedding，所以 RAG 的 Embedding 推荐通义 text-embedding-v3 或智谱 embedding-3；创建知识库的 Embedding 模型要与检索节点一致，换模型需重新索引。

## 8. 防幻觉机制（本项目最大亮点，必考）

三层：
1. **检索侧**：score_threshold 过滤 + reranking + top_k 控制 → 保证进入提示词的上下文是"高相关、有依据"的
2. **提示词侧**：system 提示词硬性规定——只能依据【上下文】回答；无依据必须明确回复"知识库中暂未找到相关信息，建议联系 IT 服务台或提交工单"；禁止编造；回答末尾必须标注「引用：[文档名]」
3. **路由侧**：if-else 判断检索结果为空 → 不硬答，走 llm_fallback 兜底转人工

一句话总结面试表达：「我们从检索质量、生成约束、结果路由三个环节分别设防，把幻觉从机制上掐掉——检索不到就明确说检索不到，而不是编一个答案。」

## 9. 数据层（演示数据）

- 虚构企业「云帆科技」（YF-Suite 协同平台 + YF-GW2000 智能网关），12 篇文档、5 大分类
- 分类：01 产品说明书（2）、02 技术文档（2）、03 IT 运维 SOP（4：Windows 故障/网络故障/VPN 配置/邮箱问题）、04 售后流程（2）、05 FAQ（2）
- 导入方式：`deploy/scripts/seed-kb.py`（Dify Service API）+ `seed-config.json` 映射 → 一键创建 5 数据集并上传文档，脚本输出数据集 ID 填入 DSL 的 dataset_ids

## 10. 校验与测试（工程质量，面试可说）

```bash
python scripts/validate_seed.py   # 知识库种子数据：48 PASS / 0 FAIL（12 篇，约 12,217 字符）
python scripts/validate_dsl.py    # 应用 DSL：30 PASS / 0 FAIL（含 graphon 引擎 schema 真实验证）
```

- validate_seed：检查文档数量/命名/标题/正文长度/编码等
- validate_dsl：用 Dify 的 graphon 引擎真实校验 DSL 结构、节点类型、连线、必填字段
- 测试报告 docs/TEST_REPORT.md：静态扫描证实项目改造层无国外网络硬依赖；Docker 启动与真实模型调用需在部署环境执行（如实披露）

## 11. 部署方式（面试能背出步骤）

前置：Docker + Compose v2.24+，内存 ≥ 4 GiB

```bash
git clone --depth 1 https://github.com/langgenius/dify dify   # 平台本体
cp deploy/docker/.env.enterprise.example dify/docker/.env      # 企业环境配置
cd dify/docker && docker compose up -d                          # 启动
# 浏览器访问 http://localhost/install 初始化管理员
```

**初始化清单**：接入模型（LLM/Embedding/Rerank）→ 创建知识库（或 seed-kb.py 一键导入）→ 导入应用 DSL → 把 dataset_ids 替换为实际 ID → 工作流两个 LLM 节点选择模型 → 发布（Web App/嵌入/服务 API）

**验证清单**：compose ps 全 up → 模型连通 → 知识库命中测试 → 问"VPN 连接超时怎么办"有引用 → 问"今天天气"走兜底

## 12. 国产化适配（结合用户背景，突出价值）

| 环节 | 优化 |
| --- | --- |
| Docker 镜像 | `deploy/docker/daemon.mirrors.example.json` 加速器模板（提速 5-10 倍） |
| 模型接口 | Dify 平台本身即 AI Provider 抽象层，支持 40+ 供应商；控制台切换零代码：DeepSeek / 通义千问（阿里云百炼）/ 智谱 AI / 月之暗面 |
| 数据与资源 | 全本地化：无国外图片/文件存储/CDN |
| 部署方案 | A 国内服务器 / B 国内云平台 / C 本地 Docker |
| 环境变量 | `.env.example` 覆盖全部配置 |

**模型组合推荐（面试能说）**：对话 LLM 用 DeepSeek / 通义 / 智谱 / 月之暗面；Embedding 用通义 text-embedding-v3 或智谱 embedding-3；Rerank 可选通义/智谱托管版。注意 DeepSeek 无 Embedding。

**国内访问风险审查结论（docs/CN_ACCESS_REVIEW.md）**：高（Docker Hub 镜像、国外模型接口）→ 已优化；中（GitHub 拉取、插件市场/更新检查）→ 加速通道/可关闭；低（pip）→ 清华镜像。

## 13. 改造边界与复用率（作品集项目的说服力）

- 上游平台能力复用：100%，未改一行上游代码
- 新增代码量：约 400 行（validate_seed.py + validate_dsl.py + seed-kb.py）
- 其余交付为 YAML 配置 / Markdown 文档
- 全部改造落在配置+数据+文档三层，可回滚、可跟随上游升级，许可证遵循上游（保留 Dify 标识）

## 14. 演示体验站（作品集加分项）

- **在线功能演示站**（doubao-html 链接）：前端真实执行「检索→命中/兜底路由→回答+引用来源」，内置 12 篇文档数据；演示模式为本地检索+模板化回答（非真实 LLM），与线上 Dify 应用路由逻辑对应
- **项目展示页**：作品集介绍页（背景/架构/功能/截图）
- 本地文件：demo/企业知识助手-功能演示.html（单文件、零依赖、离线可用）、showcase/企业知识助手-项目展示.html
- demo 检索算法：中文 bigram（滑动窗口）+ 英文整词 + 停用词过滤；相似度=交集/查询 gram 数；标题段加权；阈值 0.30；top3；附自检脚本 demo/check_demo.py（6 用例：5 命中 + 1 兜底）

## 15. 面试高频问题与答题要点

1. **介绍一下你的项目** → 一句话定位 + 痛点 + 方案 + 成果（引用第 1/3/5 节）
2. **RAG 是什么？为什么用 RAG？** → 检索增强生成；解决私有知识 + 幻觉；讲 pipeline 和三个参数
3. **怎么减少 AI 幻觉？** → 三层机制（检索/提示词/路由），逐层讲
4. **Dify 是什么？你改了什么？** → LLM 应用开发平台；配置+数据+文档层改造，没动源码，复用率 100%
5. **工作流怎么设计的？** → 7 节点图：start→检索→if-else→LLM 回答/兜底
6. **为什么用多个数据集？** → 按业务分类管理，可独立更新/权限；多路检索
7. **引用来源怎么实现的？** → retriever_resource 特性 + 提示词强制标注
8. **对话历史怎么实现的？** → memory.window enabled, size=10
9. **国内部署怎么做？** → 镜像加速 + 国产模型 + 三方案（第 12 节）
10. **如果检索质量不好怎么办？** → 调 score_threshold/top_k/rerank；换 Embedding 模型重新索引；优化文档分段
11. **和 LangChain 有什么区别？** → Dify 是可视化平台（低代码，工作流/KB/模型管理开箱即用），LangChain 是代码框架；本项目建设在 Dify 上，实施工程师视角看重平台化交付
12. **这个项目你自己的贡献？** → 架构分析、方案设计、知识库数据、DSL 编排、部署配置、校验脚本、文档与演示站

## 16. 练习题（巩固用，附答案在文末）

见仓库 `docs/` 配套练习（对话中随分段讲解后给出）。
