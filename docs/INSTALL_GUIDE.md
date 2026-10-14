# 安装部署指南（陌生人照着就能装）

> 面向第一次拿到本项目的人：从零开始，每一步做什么、看到什么、怎么判断成功、出问题怎么办。

---

## 前置准备（3 项，没做这些后面全卡）

| 要装什么 | 怎么装 | 验证成功 |
| --- | --- | --- |
| Docker Desktop（Windows 版） | 官网下载安装包，一路下一步；装完自动启用 WSL2 | 终端敲 `docker --version` 出版本号；Docker Desktop 图标显示 running |
| Docker Compose v2.24+ | Docker Desktop 自带 | `docker compose version`（空格不是横杠） |
| Git | 官网下载装好 | `git --version` |

硬件：CPU ≥ 2 核、内存 ≥ 4 GiB（推荐 8 GiB）。内存不够，后面容器起不来。

---

## 第 1 步：拉本项目（作品集仓库）

```bash
git clone https://github.com/xingjianlu573-dot/qiyexmzhishikuzhushou.git eai
cd eai
```

看到 `deploy/`、`seed/`、`scripts/`、`docs/` 这几个文件夹，说明拉对了。

## 第 2 步：拉 Dify 平台本体（上游，本项目不改它）

```bash
git clone --depth 1 https://github.com/langgenius/dify dify
```

`--depth 1` 只拉最新版，省时间。当前目录下多了一个 `dify/` 文件夹，里面有 `docker/` 子目录。

## 第 3 步：用项目企业配置覆盖 Dify 默认配置

```powershell
# Windows PowerShell
Copy-Item deploy\docker\.env.enterprise.example dify\docker\.env
```

```bash
# Git Bash / Linux / macOS
cp deploy/docker/.env.enterprise.example dify/docker/.env
```

Dify 自带的 `.env.example` 是通用版，项目提供的 `enterprise.example` 已按企业场景调好。成功判断：`dify/docker/.env` 文件存在。

## 第 4 步：启动 Docker（第一次最慢）

```bash
cd dify/docker
docker compose up -d
```

看到 `Pulling xxx`、`Downloading`、`Pulled`，最后 `Container xxx Started`。第一次拉镜像 10-30 分钟。

**国内加速（必做）**：打开 `C:\Users\你的用户名\.docker\daemon.json`（没有就新建），加上：

```json
{ "registry-mirrors": ["https://docker.m.daocloud.io"] }
```

保存后重启 Docker Desktop。项目里有模板：`deploy/docker/daemon.mirrors.example.json`。

**成功判断**：

```bash
docker compose ps
```

所有状态列显示 `running` 或 `healthy`（api、web、worker、db、redis、weaviate、nginx 等）。

## 第 5 步：浏览器初始化

打开 `http://localhost/install`，设置管理员邮箱和密码，登进 Dify 控制台。

## 第 6 步：接模型（LLM + Embedding 必须有）

控制台 → 头像 →「设置」→「模型供应商」。

| 类型 | 推荐 | 去哪里拿 Key |
| --- | --- | --- |
| LLM（对话） | DeepSeek-V3 / 通义千问 / 智谱 GLM | 对应开放平台 |
| Embedding（向量化） | 通义 text-embedding-v3 / 智谱 embedding-3 | 同上 |
| Rerank（重排，可选推荐） | 通义/智谱托管版 rerank | 同上 |

**关键坑**：DeepSeek 和月之暗面不提供 Embedding 服务。对话可以用 DeepSeek，Embedding 必须单独配通义或智谱。配完点保存，Dify 自动测连通性，绿色对勾才算过。

## 第 7 步：建知识库（二选一）

**方式 A 手动建**：控制台 →「知识库」→ 创建 5 个数据集（产品说明书、技术文档、IT 运维 SOP、售后流程、FAQ），把 `seed/knowledge-base/` 下对应 markdown 拖进去。

**方式 B 脚本一键导入（推荐）**：

1. 控制台 →「知识库」→「API 访问」→ 创建 API Key（`dataset-` 开头）
2. 回项目根目录：

```bash
pip install requests
python deploy/scripts/seed-kb.py --base-url http://localhost/v1 --api-key dataset-你的key
```

3. 脚本自动建 5 个数据集、上传 12 篇文档，最后打印 5 个数据集 ID，复制备用。

## 第 8 步：导入应用 DSL

控制台 →「工作室」→「导入 DSL」→ 选 `seed/apps/enterprise-ai-knowledge-assistant.yml`。导入后画布上有 7 个节点：开始 → 知识库检索 → 条件判断 → LLM 回答/兜底 → 输出。

## 第 9 步：绑定数据集 + 选模型

点「企业知识库检索」节点 → 把 `dataset_ids` 改成第 7 步脚本打印的真实 ID。再点两个 LLM 节点（`llm_answer`、`llm_fallback`）→ 各选一个已接好的对话模型（如 DeepSeek-V3）。

## 第 10 步：发布 + 验证

点右上角「发布」拿到 Web App 链接。

| 验证项 | 怎么做 | 预期 |
| --- | --- | --- |
| 服务全 up | `docker compose ps` | 全 running/healthy |
| 模型连通 | 控制台模型供应商页 | 绿色对勾 |
| 知识库命中 | 知识库里对任一篇提问 | 返回相关分段 + 相似度分数 |
| 应用对话 | 问"VPN 连接超时怎么办" | 回答带「引用」卡片 |
| 兜底路由 | 问"今天天气怎么样" | 走兜底，提示转人工/工单 |

---

## 常见报错排坑

| 现象 | 原因 | 一句话解决 |
| --- | --- | --- |
| 拉镜像超时 | 国内拉 Docker Hub 慢 | 配 registry-mirrors 用 daocloud |
| 容器起一半退出 | 内存不够 | Docker Desktop 内存调到 6 GiB 以上 |
| 模型调用 401/403 | API Key 错或模型名错 | 控制台重新填 Key、选对模型 |
| 知识库提问检索不到 | 索引没建完或阈值太高 | 等索引 completed；调试时 score_threshold 从 0.5 降到 0.3 |
| 回答没有引用卡片 | 没开 retriever_resource | DSL 里 `retriever_resource.enabled: true`，确认是高级对话应用 |
| seed-kb.py 报 401 | API Key 不对 | 用「知识库 → API 访问」生成的 `dataset-` 开头的 key |

---

## 面试现场演示策略

面试官 5 分钟内不会等你从零拉 30 分钟镜像。

**情况 A（最常见）：让你看项目跑起来什么样**
提前装好、镜像预拉、`docker compose up -d` 已跑着。现场直接打开浏览器演示：问"VPN 超时"看引用卡片 → 问"今天天气"看兜底 → 切知识库页 → 切工作流画布。
话术："部署我本地已经跑通了，5 个服务全 healthy，直接给你看效果。"

**情况 B：让你现场装**
提前 `docker compose pull` 把镜像全拉到本地。现场 `docker compose up -d`，因为镜像已在本地，10 秒内全部起来。
话术："我镜像之前预拉过了，启动很快。整个流程就是 clone 上游 → 覆盖企业 .env → compose up → 初始化 → 接模型 → 导知识库和 DSL → 发布，10 步。"

**情况 C：现场电脑没 Docker**
打开在线演示站（纯前端模拟，无需后端）：
`https://4kysy3b9xsj4q.doubaoapps.com/app/app_17ff8q3up6t`
话术："真实 Dify 部署我本地跑通过了；这是我单独做的可分享演示站，把核心交互（检索→路由→引用）用纯前端模拟出来，方便随时演示。"
