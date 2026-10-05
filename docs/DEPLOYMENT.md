# 部署方式（Docker Compose）

## 1. 环境要求

- Docker + Docker Compose v2.24.0+（官方要求）。
- CPU ≥ 2 核，内存 ≥ 4 GiB（推荐 8 GiB）。
- 可访问 Docker Hub 拉取镜像（国内可配置 registry mirror）。

## 2. 部署步骤

```bash
# 1) 获取上游 Dify（本仓库为改造层，平台本体直接使用官方镜像，无需源码）
git clone --depth 1 https://github.com/langgenius/dify dify

# 2) 应用企业环境配置（本仓库提供的覆盖文件）
cp deploy/docker/.env.enterprise.example dify/docker/.env

# 3) 启动（首次拉取镜像耗时较长）
cd dify/docker
docker compose up -d

# 4) 初始化
# 浏览器访问 http://localhost/install ，按向导创建管理员账号
```

## 3. 初始化配置清单

| 步骤 | 说明 |
| --- | --- |
| 1. 接入模型 | 控制台 → 设置 → 模型供应商：配置 LLM（如 DeepSeek / OpenAI 兼容 / 火山方舟 / Ollama）、Embedding（如 text-embedding-3、bge-m3）、Rerank（可选，推荐 bge-reranker 类） |
| 2. 创建知识库 | 控制台 → 知识库 → 创建，或运行导入脚本一键创建（见下） |
| 3. 导入应用 | 控制台 → 应用 → 导入 DSL：`seed/apps/enterprise-ai-knowledge-assistant.yml` |
| 4. 绑定数据集 | 打开应用 → 编辑 →「企业知识库检索」节点：将 `dataset_ids` 替换为实际数据集 ID（导入脚本会打印） |
| 5. 配置模型 | 工作流中两个 LLM 节点选择已接入的模型；检索节点按需选择 Rerank 模型 |
| 6. 发布 | 点击「发布」，可获取 Web App 链接 / 嵌入代码 / 服务 API |

## 4. 一键导入演示数据

```bash
# 在「知识库 → API 访问」创建数据集 API Key（dataset- 开头）
pip install requests
python deploy/scripts/seed-kb.py --base-url http://localhost/v1 --api-key dataset-xxxxxxxx
# 脚本输出 5 个数据集 ID，复制到 DSL 的 dataset_ids 即可
```

## 5. 验证清单（部署完成自检）

- [ ] `docker compose ps` 全部服务 healthy/up（api、web、worker、db、redis、weaviate、nginx…）
- [ ] 控制台可登录，模型供应商连通性测试通过
- [ ] 知识库命中测试：对任一篇文档提问，返回相关分段且显示相似度分数
- [ ] 应用对话：提问"VPN 连接超时怎么办"，回答附「引用」与引用卡片
- [ ] 提问与知识库无关的问题（如"今天天气"），走兜底应答（转人工指引）

## 6. 常见问题

| 现象 | 处理 |
| --- | --- |
| 镜像拉取慢 | 配置 Docker registry mirror（如 docker.m.daocloud.io） |
| 模型调用报错 | 控制台 → 模型供应商重新校验 API Key 与模型名 |
| 检索无结果 | 检查知识库索引状态（completed），降低 score_threshold 或关闭重排测试 |
| 引用卡片不显示 | 确认应用高级对话模式 + DSL 中 `retriever_resource.enabled: true` |
