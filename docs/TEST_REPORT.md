# 测试报告（中国大陆访问优化）

> 测试日期：2026-10-05 · 项目版本：改造层 v1（commit 779d5ff 基础上新增国内优化）
> 测试环境：Windows 10/11 + Python 3.14.7（本机，非中国大陆网络）；Docker 未安装

## 1. 测试范围

| 项 | 方法 | 结论 |
| --- | --- | --- |
| 知识库种子数据 | `python scripts/validate_seed.py` | ✅ 48 PASS / 0 FAIL（12 篇文档，约 12,217 字符） |
| 应用 DSL | `python scripts/validate_dsl.py` | ✅ 30 PASS / 0 FAIL（含 graphon 引擎 schema 真实验证） |
| Python 脚本编译 | `python -m py_compile`（validate_seed / validate_dsl / seed-kb） | ✅ 3 个脚本全部通过 |
| JSON 配置 | `json.load`（daemon.mirrors.example.json / seed-config.json） | ✅ 均合法 |
| 前端资源 | 全项目 URL 静态扫描 | ✅ 无 CDN / npm / 国外图片 / 第三方 JS 依赖 |
| 示意图 HTML | `src=/href=` 外链扫描 | ✅ 0 处外部资源引用（纯 CSS + 系统字体） |
| 网络可达性 | 443 端口探测（本机） | 见第 3 节 |

## 2. 核心功能（静态验证）

| 功能 | 验证方式 | 结论 |
| --- | --- | --- |
| 文档上传 / 知识库管理 | `seed-kb.py` 逻辑 + seed-config 映射 | ✅ 5 数据集一键建库（需真实部署后执行） |
| RAG 检索 | DSL knowledge-retrieval 节点（top_k=5 / 阈值 0.5 / 重排） | ✅ 配置经 graphon 校验 |
| AI 问答 + 引用来源 | DSL llm 节点 + retriever_resource 特性 | ✅ 配置经 graphon 校验 |
| 对话历史 | DSL memory 窗口（10 轮） | ✅ 配置经 graphon 校验 |
| 兜底转人工 | DSL if-else + llm_fallback 分支 | ✅ 配置经 graphon 校验 |

## 3. 网络可达性检查（中国大陆访问优化项）

> ⚠️ 本机位于欧洲网络，以下结果仅证明**域名解析与 443 端口服务存活**；中国大陆境内实测需在境内网络复测（推荐：部署后在云服务器执行 `curl -I <地址>` 复核）。

| 目标 | 用途 | 443 可达（本机） |
| --- | --- | --- |
| docker.m.daocloud.io | Docker 镜像加速器（示例） | ✅ True |
| api.deepseek.com | DeepSeek 模型 API | ✅ True |
| open.bigmodel.cn | 智谱 AI 开放平台 | ✅ True |
| dashscope.aliyuncs.com | 阿里云百炼（通义千问） | ✅ True |
| platform.moonshot.cn | 月之暗面 Kimi | ✅ True |
| pypi.tuna.tsinghua.edu.cn | pip 清华镜像 | ✅ True |
| ghproxy.com | GitHub 加速通道（示例） | ✅ True |

## 4. 未执行项（如实披露）

| 项 | 原因 |
| --- | --- |
| Docker 启动 / 容器健康 | 本机未安装 Docker；需按 README_CN.md 第 3 节在服务器/本机执行 |
| AI 接口真实调用 | 需真实 API Key 与部署实例；本报告仅验证域名可达 |
| 中国大陆网络实测 | 本机不在境内网络；部署后按 README_CN.md 自检清单复核 |

## 5. 部署后自检清单（对应 README_CN.md 第 3、4 节）

- [ ] `docker compose up -d` 成功，`docker compose ps` 全部 up
- [ ] 镜像加速器生效：`docker info` 的 Registry Mirrors 显示配置地址
- [ ] 控制台添加国产模型供应商并校验通过
- [ ] 知识库导入完成，命中测试返回相关分段
- [ ] 应用发布后提问「VPN 连接超时怎么办」得到带引用的回答；无关问题走兜底

## 6. 结论

- 项目改造层**自身无国外网络硬依赖**（静态扫描证实）。
- 国内访问优化交付物（镜像加速模板、国产模型文档、.env.example、README_CN）均已生成并通过语法/结构校验。
- 剩余风险集中于**真实部署执行**（Docker 拉镜像速度、模型 API 可用性、境内网络表现），需按自检清单在目标环境验证；本报告所有"可静态验证"项均已通过。
