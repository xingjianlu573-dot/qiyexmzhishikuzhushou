# 中国大陆访问风险审查报告

> 审查对象：本项目改造层全部文件（`analysis/ docs/ seed/ deploy/ scripts/ screenshots/ README.md`）
> 审查方法：全项目 URL 静态扫描 + 依赖清单核对 + 上游 Dify 部署链路核查
> 审查日期：2026-10-05

## 1. 结论速览

| 层 | 是否存在国外依赖 | 风险等级 | 说明 |
| --- | --- | --- | --- |
| 本项目前端 | 无 | 低 | 本项目不含前端页面代码；唯一页面为 `screenshots/` 下 3 个示意图 HTML（纯 CSS/系统字体，无 CDN/无外链 JS/无图片外链） |
| 本项目脚本 | requests（PyPI） | 低 | 可通过国内 pip 镜像安装；其余脚本仅用 Python 标准库 |
| 本项目数据/文档 | 无 | 低 | 12 篇演示文档全部本地化；URL 均为虚构示例域名（yfcloud.cn / gw2000.local） |
| 上游 Dify 镜像 | Docker Hub | **高** | `langgenius/dify-api:1.17.1`、`dify-web`、weaviate、postgres 等镜像默认从 Docker Hub 拉取，中国大陆直连慢/易失败 |
| 上游 Dify 模型接口 | OpenAI 等国外供应商 | **高** | 默认模型供应商在控制台配置；若沿用 OpenAI 需特殊网络，须切换为国内模型 |
| 上游 Dify 外围站点 | marketplace.dify.ai / updates.dify.ai | 中 | 插件市场与更新检查走国外域名；不影响核心问答功能 |
| GitHub 获取 | github.com | 中 | 拉取上游与查看本项目受网络影响；有替代通道（加速镜像/国内 Gitee） |

## 2. 逐项检查结果

### 2.1 前端访问问题

| 检查项 | 结果 |
| --- | --- |
| CDN | 无。示意图 HTML 未引用任何 CDN 资源 |
| 静态资源 | 无。示意图无图片/字体外链，字体使用系统字体栈 |
| npm 依赖 | 无。本项目无 package.json |
| 第三方 JS | 无。示意图仅内联 CSS |
| 说明 | 真正的前端（Dify Web）由上游镜像提供，Next.js 构建产物自托管，无运行时国外 CDN 依赖 |

### 2.2 后端服务问题

| 检查项 | 结果 |
| --- | --- |
| API 访问 | 本项目无后端代码；Service API 调用地址可由 `--base-url` 指定为内网/公网地址 |
| 跨域 | 上游 Dify 支持 `WEB_API_CORS_ALLOW_ORIGINS` / `CONSOLE_CORS_ALLOW_ORIGINS` 配置，国内部署按需设置 |
| 网络请求 | 知识库导入脚本仅请求 Dify Service API（本机/内网），无国外请求 |
| 第三方接口 | 无 |

### 2.3 AI 服务问题

| 检查项 | 结果 |
| --- | --- |
| OpenAI API 依赖 | 上游默认示例含 `OPENAI_API_BASE=https://api.openai.com/v1`（docker/.env.example）；本项目不依赖，且明确支持替换 |
| 国外模型接口 | 风险点：若部署时接入 OpenAI 系模型，中国大陆无法直连。**解决方案：切换国内模型供应商**（见 docs/CN_MODEL_PROVIDERS.md） |
| Embedding / Rerank | 同上，须选择国内可访问的 embedding/rerank 模型（DeepSeek 不提供 embedding，需搭配通义/智谱/BGE 系等） |
| 向量数据库 | Weaviate 为本地容器，无国外依赖；可切换 Qdrant / pgvector 等，均本地化 |

### 2.4 部署问题

| 检查项 | 结果 |
| --- | --- |
| Docker 镜像来源 | Docker Hub。**最高风险项**：须配置镜像加速器（daemon.json）或使用镜像仓库替代 |
| Docker Hub 访问速度 | 中国大陆直连不稳定，须加速 |
| GitHub Actions | 本项目未配置 CI；不构成访问风险 |
| 云服务器部署 | 国内云主机（阿里云/腾讯云）默认可访问 Docker Hub（需加速）与国内模型接口 |

## 3. 风险分级汇总

- **高**（影响核心使用）：Docker Hub 镜像拉取慢；模型供应商需切换为国内可直连服务。
- **中**（影响体验）：GitHub 获取慢；Dify 插件市场/更新检查域名（可配置关闭或忽略）。
- **低**（可接受）：pip 安装 requests（国内镜像可加速）；其余无。

## 4. 优化策略（对应交付物）

| 风险 | 优化措施 | 交付物 |
| --- | --- | --- |
| Docker Hub 慢 | 镜像加速器 daemon.json 模板 + 部署文档 | `deploy/docker/daemon.mirrors.example.json`、`README_CN.md` |
| GitHub 拉取慢 | 镜像/加速通道说明 + Gitee 替代方案 | `README_CN.md` |
| 国外模型 | 国内模型供应商接入文档（DeepSeek/通义/智谱/月之暗面）+ 控制台配置步骤 | `docs/CN_MODEL_PROVIDERS.md`、`.env.example` |
| 外围站点慢 | 说明可关闭更新检查/插件市场（不影响核心功能） | `README_CN.md` |
| 部署落地 | 方案 A 国内服务器 / B 国内云平台 / C 本地 Docker | `README_CN.md` |
