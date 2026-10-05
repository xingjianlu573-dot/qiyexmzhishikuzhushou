# YF-Suite OpenAPI 集成指南

文档编号：TD-YF-010  
维护部门：技术架构部  
最后更新：2026-09-02

## 1. 概述

YF-Suite 提供完整的 RESTful OpenAPI，供第三方系统与企业内部应用集成。所有接口基于 HTTPS，数据格式为 JSON，认证采用 OAuth 2.0（Client Credentials）。

## 2. 认证方式

1. 管理员在"开放平台"中创建应用，获取 `client_id` 与 `client_secret`。
2. 调用令牌接口获取 access_token：

```
POST https://{host}/openapi/v1/token
Content-Type: application/json

{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "grant_type": "client_credentials"
}
```

3. access_token 有效期 2 小时，请在有效期前 10 分钟刷新；所有业务接口请求头携带 `Authorization: Bearer {access_token}`。

## 3. 常用接口

### 3.1 获取组织架构
`GET /openapi/v1/org/tree?with_member=true`  
返回组织树及成员列表，用于外部系统同步通讯录。

### 3.2 发送消息
`POST /openapi/v1/message/send`  
请求体：`{"to_type": "user|department|group", "to_ids": ["u001"], "content": "..."}`  
支持 24 小时内撤回（`POST /openapi/v1/message/recall`）。

### 3.3 发起审批
`POST /openapi/v1/approval/create`  
请求体包含表单数据与流程标识，创建成功后返回 `approval_no`。

### 3.4 查询知识文档
`GET /openapi/v1/knowledge/docs?keyword={kw}&page=1&page_size=20`  
仅返回当前账号有阅读权限的文档。

## 4. 错误码约定

| 错误码 | 说明 |
| --- | --- |
| 401 | token 无效或过期 |
| 403 | 无接口权限或数据权限 |
| 429 | 调用频率超限（默认 100 次/分钟） |
| 500 | 服务内部错误 |

## 5. 沙箱与联调

- 提供 `https://sandbox.yfcloud.cn` 沙箱环境，数据与生产隔离。
- 联调账号请联系技术架构部申请，沙箱内每日限流 10,000 次。

## 6. 调用规范

- 幂等：写操作请携带 `Idempotency-Key` 请求头，重复提交不会产生重复数据。
- 限流：单应用默认 100 次/分钟，突发流量请提前申请配额。
- 日志：平台记录全部调用审计日志，保留 180 天。
