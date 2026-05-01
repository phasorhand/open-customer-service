# OpenCS Superpowers 设计评审 01

评审对象：`docs/superpowers/specs/2026-04-30-open-cs-mvp-architecture.md`

评审日期：2026-04-30

## 总体结论

当前设计方向成立，但进入 `writing-plans` 前建议先修改几处关键设计。主要风险集中在四类：Tool 执行边界不够硬、CRM UI fallback 探索可能对生产数据产生副作用、客服外发文案审批策略偏宽、MVP 范围过大。

## Findings

### 1. [P1] Tool 调用缺少强制 Guard 执行边界

位置：`docs/superpowers/specs/2026-04-30-open-cs-mvp-architecture.md:139-152`

文档说所有副作用都走 ActionGuard，但 ToolProvider 暴露的是 `Tool.call(args)`，同时 API 调用被描述为进程内执行。这会让自动生成的 CRM/MCP 写工具有机会绕过 Harness。

建议修改：

- 把 Harness 设计成唯一执行入口。
- Agent 只能生成 `ActionPlan`，不能直接调用 provider。
- ActionGuard 负责分类、审批、签发执行令牌。
- 只有拿到执行令牌后，运行时才调用具体 `ToolProvider`。

### 2. [P1] UI fallback 探索不应在生产 CRM 上模拟写操作

位置：`docs/superpowers/specs/2026-04-30-open-cs-mvp-architecture.md:267-286`

CRM Explorer 使用 super-token 登录后遍历 CRM，并模拟查客户、改字段。UI 工具的 `dry_run` 很难证明无副作用，生产环境探索写路径风险很高。

建议修改：

- 要求测试租户、沙箱环境或只读账号作为默认探索条件。
- 生产 UI fallback 只允许发现页面结构和只读验证。
- 写工具必须手工确认，并在非生产环境回放通过后再启用。
- super-token 只能用于短期探索任务，且需要完整审计。

### 3. [P1] 外发文案默认异步审核风险过高

位置：`docs/superpowers/specs/2026-04-30-open-cs-mvp-architecture.md:147-152`

Orange 把外发文案设为自动执行加异步审核，但客服回复本身就是客户侧副作用。模型自由生成内容可能包含承诺、价格、退款、法律或合规表述，事后审核无法阻止已经发出的风险内容。

建议修改：

- MVP 区分模板化低风险回复和自由生成回复。
- 模板化低风险回复可进入自动发送路径。
- 自由生成外发在早期默认同步 HITL。
- 若要自动发送，至少要求置信度、敏感词、承诺检测、金额检测全部通过。

### 4. [P2] Memory 写入全走 Evolution 会卡住会话状态

位置：`docs/superpowers/specs/2026-04-30-open-cs-mvp-architecture.md:130-137`

`WORKING.md` 是当前会话短期状态，如果所有写入都走 Proposal/Evolution，会把普通对话状态更新变成异步审批或后台流程，影响实时对话。

建议修改：

- 拆成 raw event store、ephemeral session state、long-term memory consolidation 三层。
- 当前会话状态可以实时写入。
- 长期记忆沉淀和客户画像变更才走 Proposal。
- PII、金额、承诺、客户画像关键字段继续保持 HITL。

### 5. [P2] MVP 范围过宽，实施计划风险高

位置：`docs/superpowers/specs/2026-04-30-open-cs-mvp-architecture.md:333-346`

P0 同时包含企微、WebChat、OCR、3 worker、learned skills、FTS + 向量、API/UI/MCP 三类工具、CRM 自动探索、完整 Evolution、HITL UI、Dashboard 和 Compose，范围接近 v1。

建议修改：

- MVP 收缩为企微/WebChat、Agent Core、只读 CRM API 工具、ActionGuard、HITL 外发、AuditLog。
- UI fallback、MCP、自动 skill 沉淀和完整 Evolution 推到后续阶段。
- 先跑通可审计的客服闭环，再逐步打开自进化和自动探索能力。

## 额外建议

`docs/superpowers/specs/2026-04-30-open-cs-mvp-architecture.md:257` 中“会话存档 API 兜底”建议改成“可选合规留存能力”，不要当成默认兜底路径。企微客服接收消息和发送消息本身已有独立 API 流程，会话内容存档是另一类合规能力。

参考：

- [企业微信接收消息和事件](https://open.work.weixin.qq.com/api/doc/90000/90135/94670)
- [企业微信发送消息](https://open.work.weixin.qq.com/api/doc/90000/90135/94677)
- [企业微信获取会话内容](https://developer.work.weixin.qq.com/document/path/91774)

## 建议优先级

1. 先改 Tool/Harness 执行边界。
2. 再收紧 CRM Explorer 的生产探索策略。
3. 同步调整外发文案审批策略。
4. 拆清 Memory 的实时状态和长期沉淀。
5. 最后重切 MVP 范围，再进入实施计划拆解。
