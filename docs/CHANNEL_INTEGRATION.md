# 多渠道接入指南（IM 集成）

> 目标：让 Enterprise AI Knowledge Assistant 不止于网页问答，还能在企业常用 IM 内直接使用——企业微信、飞书、钉钉、微信公众号等。
> 定位：渠道层是"前端"；知识库、工作流、防幻觉、引用来源全部复用现有 DSL，改造边界（配置 + 数据 + 文档）不变。
> 参考：RAGFlow Chat Channels、WeKnora IM 集成、Dify Marketplace 与 dify-on-wechat 生态。

---

## 1. 为什么做多渠道（作品集叙事）

| 现状 | 多渠道后 |
| --- | --- |
| 员工/客服需打开浏览器访问 Web App | 在企微/飞书/钉钉群里直接提问，零切换 |
| 高频问题仍要"跳转网页"这一步 | 对话即入口，一线使用门槛最低 |
| 演示只覆盖 Web 端 | 覆盖 IM 端，展示"平台化接入能力" |

**核心结论**：Dify 应用发布为 Service API 后，所有渠道本质都是"调用同一个聊天 API"。渠道接入 = 消息收发的适配，不改变应用本身。

## 2. 三种接入模式对比

| 模式 | 方案 | 工作量 | 公网要求 | 适用 |
| --- | --- | --- | --- | --- |
| A | Dify Marketplace 官方插件（企微群机器人 / 公众号） | 最小（控制台操作） | 视渠道而定 | 快速上线企微/公众号 |
| B | 机器人桥接项目（dify-on-wechat / dify-on-dingtalk） | 中（部署一个 Python 服务） | 长连接免公网 | 个人微信 / 多端统一 |
| C | 自建事件网关（飞书/企微自建应用 + 回调服务） | 中高（自写回调 + 调 API） | Webhook 需公网；长连接免公网 | 深度定制、权限分级 |

> 三种模式可并存（如：企微走插件、飞书走自建网关），互不冲突。

## 3. 前置：把应用发布为 Service API

1. 控制台打开 **Enterprise AI Knowledge Assistant** →「访问 API」。
2. 创建 API 密钥（`app-` 开头），记录：
   - `API_BASE`：如 `http://localhost/v1`（公网部署用域名）
   - `API_KEY`：`app-xxxxxxxx`
3. 聊天接口（所有渠道最终都调它）：

   ```
   POST {API_BASE}/chat-messages
   Authorization: Bearer {API_KEY}
   Content-Type: application/json

   {
     "query": "VPN 连接超时怎么办？",
     "response_mode": "blocking",
     "user": "user-<渠道用户标识>"
   }
   ```

   > 返回中的 `answer` 即 AI 回答；若启用了引用来源，消息体携带 `retriever_resources`（引用卡片数据）。

## 4. 模式 A：Dify Marketplace 插件（企微群机器人为例）

1. 控制台 →「插件」→ Marketplace，安装 **WeCom** 插件（langgenius/wecom）。
2. 在企业微信群里「群设置 → 群机器人 → 添加机器人」，复制 Webhook 地址。
3. 在插件配置中填入 Webhook，绑定 **Enterprise AI Knowledge Assistant** 应用。
4. 群里 @机器人 提问即可收到基于知识库的回答。

> 微信公众号同理：安装 `dify_wechat_plugin`（订阅号，需通过公众号平台配置服务器 URL/Token）。
> 优势：全部控制台操作；劣势：能力受插件范围限制（群内提问、无会话隔离等）。

## 5. 模式 B：dify-on-wechat 桥接（个人微信 / 多端统一）

dify-on-wechat 是 chatgpt-on-wechat 的下游分支，支持将 Dify 应用接入个人微信、公众号、企微、飞书、钉钉、Telegram 等。

```bash
git clone https://github.com/hanfangyuan4396/dify-on-wechat.git
cd dify-on-wechat
pip install -r requirements.txt
cp config-template.json config.json
```

`config.json` 关键配置（对接本项目）：

```json
{
  "channel_type": "wx",              // wx=个人微信 / wechatcom_app=企微 / feishu=飞书 / dingtalk=钉钉
  "model": "dify",
  "single_chat_prefix": [""],
  "dify_api_base": "http://localhost/v1",
  "dify_api_key": "app-xxxxxxxx",
  "dify_app_type": "workflow",       // 或 chat；本项目为高级对话（chat）
  "conversation_max_tokens": 1000
}
```

运行 `python app.py`，扫码登录后即可在微信/企微/飞书等渠道与知识助手对话。

> 优势：多端统一、社区活跃、长连接无需公网 IP；劣势：是第三方桥接项目，需自行维护（本项目仅提供对接说明）。

## 6. 模式 C：自建事件网关（飞书自建应用，最灵活）

适合需要"会话隔离 + 权限分级 + 深度定制"的企业场景，也是实施能力的核心展示。

### 6.1 飞书开放平台侧

1. 飞书开放平台 → 创建**企业自建应用**，记录 App ID / App Secret。
2. 添加机器人能力；开通权限：`im:message`（接收与发送消息）、`im:message.group_at_msg`（群 @消息，可选）。
3. 事件订阅：
   - **长连接（推荐，免公网）**：飞书开放平台 → 事件订阅 → 使用长连接模式（WebSocket），无需配置回调地址。
   - **Webhook**：配置公网回调地址，如 `https://your-domain.com/feishu/callback`，并设置加密校验（Encrypt Key / Verification Token）。

### 6.2 回调服务（示例：Python + Flask，逻辑骨架）

```python
# 事件回调：im.message.receive_v1
def on_message(payload):
    msg = payload["event"]["message"]
    if msg["message_type"] != "text":
        return {"code": 0}
    text = msg["content"]  # 解析为 JSON 后取 content.text
    user_id = msg["sender"]["sender_id"]["open_id"]

    # 调用 Dify 聊天 API（见第 3 节）
    answer = dify_chat(API_BASE, API_KEY, text, f"feishu-{user_id}")

    # 回发消息
    reply_feishu(app_access_token, msg["chat_id"], msg["message_id"], answer)
```

### 6.3 会话隔离说明

- 以渠道用户标识（open_id / user_id）作为 Dify 聊天 API 的 `user` 参数 → 每个员工拥有独立会话历史（对应 DSL 的 memory 窗口）。
- 后续可扩展：按部门/岗位映射到不同数据集（数据权限分级）。

## 7. 与现有项目的衔接

| 项目交付物 | 在多渠道中的角色 |
| --- | --- |
| `seed/apps/enterprise-ai-knowledge-assistant.yml` | 无需改动；知识库检索/防幻觉/兜底/引用全部复用 |
| `seed/knowledge-base/` | 渠道共享同一知识库，内容一次更新全渠道生效 |
| 工作流（if-else 兜底转人工） | 渠道内自动路由，未命中同样引导转人工 |
| 国产化部署（README_CN / 镜像加速 / 国内模型） | 企微/飞书/钉钉均为国内服务，天然适配国内网络环境 |

## 8. 验证清单（部署后自检）

- [ ] 应用已发布，`curl` 调用 `chat-messages` 返回带引用的回答（"VPN 连接超时怎么办"）
- [ ] 企微群 @机器人 → 收到基于知识库的回答（模式 A）
- [ ] 微信/飞书发送 "电脑蓝屏了怎么处理" → 收到引用来源（模式 B/C）
- [ ] 发送无关问题（如"今天天气"）→ 收到兜底转人工指引
- [ ] 两个不同渠道用户分别提问 → 会话历史互不串扰（user 参数隔离）
- [ ] 长连接模式：无公网 IP 时渠道仍可用

## 9. 常见问题

| 现象 | 处理 |
| --- | --- |
| 渠道无响应 | 检查应用已发布、API Key 正确、模型供应商连通 |
| Webhook 模式收不到事件 | 确认回调地址公网可达、加密校验配置一致、事件已订阅 |
| 回答不带引用 | 确认渠道插件/桥接版本透传 `retriever_resources`；Web 端引用卡片与 IM 端文本标注存在差异 |
| 多人共用同一会话 | 检查 `user` 参数是否按渠道用户区分 |
| 想支持更多渠道 | 复用模式 B 的 channel_type（Telegram/Slack/QQ 等）或参考 RAGFlow/WeKnora 渠道矩阵 |
