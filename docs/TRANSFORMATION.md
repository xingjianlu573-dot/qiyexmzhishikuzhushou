# 改造方案：从 Dify 平台到 Enterprise AI Knowledge Assistant

## 1. 改造目标

在**不重构上游平台**的前提下，将 Dify 交付为一套可直接演示的**企业内部知识助手**：
员工/客服通过对话查询产品说明书、技术文档、IT 运维 SOP、售后流程与 FAQ，
AI 回答必须基于知识库内容并展示**引用来源**，检索无依据时**自动转人工**（兜底应答），从机制上减少幻觉。

## 2. 业务场景

- 使用者：企业内部员工、一线客服、IT 支持。
- 输入：自然语言问题（如"VPN 连不上怎么办""网关固件升级失败怎么处理"）。
- 输出：基于知识库的答案 + 引用来源（来源文档名/分段），未命中时给出转人工指引。

## 3. 改造内容（全部为配置 + 数据 + 文档层）

| 目录/文件 | 内容 | 对应需求 |
| --- | --- | --- |
| `seed/knowledge-base/` | 12 篇企业知识库文档（5 大分类） | 企业知识库案例、演示数据 |
| `seed/apps/enterprise-ai-knowledge-assistant.yml` | 高级对话应用 DSL：知识检索 + 防幻觉提示词 + 自动路由 + 引用来源 + 记忆 | 产品手册问答、SOP 问答、引用来源、工作流自动处理问题 |
| `deploy/docker/.env.enterprise.example` | 企业部署环境配置（Weaviate 向量库等） | 部署方式 |
| `deploy/scripts/seed-kb.py` + `seed-config.json` | 一键创建 5 个知识库并上传文档（Dify Service API） | 知识库管理、快速落地 |
| `scripts/validate_dsl.py` / `validate_seed.py` | DSL 与种子数据自动化校验 | 工程质量与可验证性 |
| `docs/` + `analysis/` + `README.md` | 架构分析、案例、部署、截图、作品集 README | 文档化交付 |

## 4. 应用工作流设计（DSL 图）

```
用户提问 (start: sys.query)
   │
   ▼
企业知识库检索 (knowledge-retrieval)
   │  多数据集（5 库）× 多路检索
   │  top_k=5 · score_threshold=0.5 · reranking=true
   ▼
检索结果判断 (if-else: result not empty ?)
   ├─ 命中 ──► LLM 基于知识库回答（防幻觉系统提示词）
   │                │  仅依据上下文；无依据即明说；末尾标注「引用：[文档名]」
   │                ▼
   │              Answer（聊天界面渲染引用卡片 retriever_resource）
   │
   └─ 未命中 ─► LLM 兜底应答（引导转 IT 服务台 / 工单 + 建议换问法）
                   │
                   ▼
                 Answer（兜底回答）
```

**防幻觉机制（三层）**：
1. **检索侧**：`score_threshold=0.5` 过滤低相关片段；`reranking=true` 二次排序；`top_k=5` 控制上下文规模。
2. **提示词侧**：系统提示词强制"仅依据上下文回答 / 无依据必须明说 / 引用来源标注 / 不编造"。
3. **路由侧**：`if-else` 判断检索结果为空 → 不硬答，走兜底转人工。

## 5. 复用率评估

- 上游平台能力复用：100%（未改一行上游代码）。
- 交付物中新增代码量：仅 2 个校验脚本 + 1 个导入脚本（约 400 行），其余为 YAML/MD/文档。
- 符合"不要重新开发、最大化复用原项目"约束。

## 6. 变更记录建议（Git）

建议按四个提交落地，见 `README.md` 的"Git 提交说明"。
