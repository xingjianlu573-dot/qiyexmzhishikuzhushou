# Enterprise AI Knowledge Assistant · 中国大陆部署指南

中文版说明文档：面向**中国大陆用户/企业**的访问优化与部署指引，使项目无需特殊网络环境即可：

- 访问 Web 界面（知识助手问答）
- 使用核心功能（文档上传 / RAG 检索 / AI 问答 / 引用来源 / 对话历史 / 知识库管理）
- 下载与运行本项目
- 使用国产大模型（DeepSeek / 通义千问 / 智谱 AI / 月之暗面）

> 项目英文主文档：[README.md](README.md) · 架构分析：[analysis/ARCHITECTURE.md](analysis/ARCHITECTURE.md)
> 风险审查：[docs/CN_ACCESS_REVIEW.md](docs/CN_ACCESS_REVIEW.md) · 模型接入：[docs/CN_MODEL_PROVIDERS.md](docs/CN_MODEL_PROVIDERS.md)

---

## 1. 国内访问优化总览

| 环节 | 默认情况 | 本项目优化后 |
| --- | --- | --- |
| Docker 镜像 | 直连 Docker Hub，慢/易失败 | 镜像加速器配置模板 + 部署指引 |
| 上游代码获取 | github.com 直连 | 加速通道 / Gitee 替代方案 |
| 模型接口 | 依赖 OpenAI 等国外服务 | 国产模型供应商（控制台即切即用） |
| 数据与资源 | — | 全部本地化（无国外图片/存储/CDN） |
| 插件市场/更新检查 | 请求国外域名 | 可关闭/忽略，不影响核心功能 |

## 2. 环境要求

- Docker + Docker Compose v2.24+；CPU ≥ 2 核，内存 ≥ 4 GiB（推荐 8 GiB）
- 国内云服务器：腾讯云 / 阿里云轻量应用服务器 2C4G 及以上即可
- 模型：任一国内大模型 API Key（见第 4 节）

## 3. 部署步骤

### 3.0 配置 Docker 镜像加速（国内必做，提速 5-10 倍）

将 `deploy/docker/daemon.mirrors.example.json` 中的地址合并到 Docker 配置：

- **Linux**：编辑 `/etc/docker/daemon.json`（合并 `registry-mirrors` 字段），执行 `sudo systemctl restart docker`
- **Docker Desktop（Windows/macOS）**：设置 → Docker Engine → 编辑 JSON → Apply & Restart

> 公共加速器地址时效性以当时可用为准；也可在阿里云/腾讯云容器镜像服务控制台获取**专属加速地址**（更稳定，推荐生产环境使用）。

### 3.1 方案 A：国内服务器部署（推荐，真实可用）

```bash
# 1) 获取上游 Dify（GitHub 慢可用加速通道，见第 5 节）
git clone --depth 1 https://github.com/langgenius/dify dify
#   或使用加速：git clone https://ghproxy.com/https://github.com/langgenius/dify dify
#   或从 Gitee 镜像仓库获取

# 2) 应用国内部署配置（本项目提供）
cp .env.example dify/docker/.env

# 3) 启动
cd dify/docker && docker compose up -d

# 4) 初始化：浏览器访问 http://<服务器IP>/install 创建管理员
# 5) 模型配置：见第 4 节；知识库导入：见第 6 节
```

### 3.2 方案 B：国内云平台部署

- **腾讯云轻量应用服务器 / 阿里云轻量服务器**：选 CentOS/Ubuntu 镜像 → 安装 Docker → 按方案 A 执行。购买时选**国内地域**（上海/广州/成都等），无需备案也可用 IP+端口访问（80 端口建议完成 ICP 备案后绑定域名）。
- **容器服务 / 自建 K8s**：将 `deploy/docker/` 中的 Compose 配置转成工作负载，注意镜像同样走加速器。
- **国内 PaaS（如 Sealos / 飞致云类平台）**：按平台引导导入 Compose 配置。

### 3.3 方案 C：本地 Docker 运行（演示/开发）

- **Windows**：安装 Docker Desktop（启用 WSL2），完成镜像加速配置后按方案 A 步骤执行；浏览器访问 `http://localhost/install`。
- **macOS / Linux**：同理。
- 适合作品集演示与个人试用；公网访问需配合内网穿透（如 frp、花生壳）或云服务器。

## 4. 国内模型配置（5 分钟）

核心原则：**Dify 平台即 AI Provider 抽象层，切换模型零代码**。

| 用途 | 推荐供应商 | 模型示例 |
| --- | --- | --- |
| 对话 LLM | DeepSeek / 阿里云百炼 / 智谱 AI / 月之暗面 | deepseek-chat、qwen-plus、glm-4-flash、moonshot-v1-8k |
| Embedding | 阿里云百炼 / 智谱 AI | text-embedding-v3、embedding-3 |
| Rerank（可选） | 阿里云百炼 / 智谱 AI | 以开放平台模型列表为准 |

步骤：控制台 → 设置 → 模型供应商 → 添加供应商（DeepSeek / 阿里云百炼 / 智谱 AI / Moonshot）→ 填入 API Key → 在应用工作流 LLM 节点与知识库检索节点选择模型。

详细接入步骤与 FAQ 见 [docs/CN_MODEL_PROVIDERS.md](docs/CN_MODEL_PROVIDERS.md)。

## 5. 下载/获取加速

| 场景 | 方式 |
| --- | --- |
| 拉取上游 Dify | GitHub 直连 / `ghproxy` 类加速前缀 / Gitee 镜像仓库 |
| 查看本项目 | GitHub 直连，或克隆到 Gitee 后国内访问 |
| pip 安装脚本依赖 | `pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple`（清华镜像） |
| Docker 镜像 | 第 3.0 节镜像加速器 |

## 6. 一键导入演示数据

```bash
pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple
# 控制台「知识库 → API 访问」创建数据集 API Key 后执行：
python deploy/scripts/seed-kb.py --base-url http://localhost/v1 --api-key dataset-xxxxxxxx
# 脚本输出 5 个数据集 ID，替换到应用 DSL 的 dataset_ids
```

## 7. 常见问题（FAQ）

| 问题 | 处理 |
| --- | --- |
| docker compose up 拉镜像超时 | 检查 daemon.json 加速器是否生效（`docker info` 查看 Registry Mirrors） |
| 首次打开 /install 白屏 | 等 nginx/web 容器就绪（`docker compose ps` 全部 up）后刷新 |
| 控制台提示模型校验失败 | 见 CN_MODEL_PROVIDERS.md 第 5 节 |
| 检索不到内容 | 知识库索引状态为「已完成」；Embedding 模型与创建时一致 |
| 想关掉国外更新检查 | `.env` 中 `CHECK_UPDATE_URL=` 置空后重启 |
| 80 端口被占用 | 修改 `.env` 中 `NGINX_PORT` / `EXPOSE_NGINX_PORT` |
| 需要 HTTPS | 在云服务器配置 Nginx/Caddy 反向代理 + 免费证书（如 Let's Encrypt） |

## 8. 测试与验证

```bash
python scripts/validate_seed.py   # 知识库种子数据：48 PASS / 0 FAIL
python scripts/validate_dsl.py    # 应用 DSL：30 PASS / 0 FAIL
```
部署后自检清单见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) 第 5 节。
