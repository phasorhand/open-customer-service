# Harness / ActionGuard · OSS 调研

## 目标
提供 OpenCS 的唯一执行入口：接收 Worker 提交的 `ActionPlan`，按风险分级（Green→Red），签发短期 `ExecutionToken`，拒绝或队列化高风险动作，并写入不可篡改的 `AuditLog`。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| [Open Policy Agent (OPA)](https://github.com/open-policy-agent/opa) | Apache-2.0 | 2026-04 | 9.6k | — | ⚠️ 借抽象 | 策略外置思路优秀；Go 服务，Python 侧需 HTTP 调用，MVP 封装成本 > 自建 |
| [casbin/pycasbin](https://github.com/casbin/pycasbin) | Apache-2.0 | 2026-03 | 2.5k | — | ❌ | 专注 RBAC/ABAC，无 ActionPlan 语义；分级策略需完全自建 |
| [PyJWT](https://github.com/jpadilla/pyjwt) | MIT | 2026-02 | 5.1k | ~130KB | ⚠️ 部分复用 | 可用于 token 签名，但 JWT 携带过多字段；我们只需 HMAC-SHA256 + 短TTL + args-hash 绑定，直接用 `cryptography` 更轻 |
| [cryptography](https://github.com/pyca/cryptography) | Apache-2.0/BSD | 2026-04 | 7.2k | ~3MB | ⚠️ 待用 | HMAC-SHA256 via stdlib 已满足 token.py 需求；`cryptography` 作为项目依赖保留，供 v1 PKI/非对称密钥操作使用，token.py 当前未引入 |

## 决策
- **自建**：stdlib `hmac` + `hashlib` —— HMAC-SHA256 原语已在 Python stdlib，无需第三方包；`cryptography` 保留为项目依赖以备 v1 非对称密钥操作
- **借抽象**：OPA 的"策略外置"思路 → 接口按策略可插拔设计，MVP 用代码实现策略，v1 切 OPA 无需改接口
- **自建**：`ActionPlan` 类型系统 + `ActionGuard` 分级逻辑 + `AuditLog` —— 产品差异化核心，无合身 OSS（§6.6 C 类）

## 集成边界
- stdlib `hmac`/`hashlib` 仅在 `token.py` 内使用；其他模块只持有 `ExecutionToken` Protocol（来自 `opencs.channel.exec_token`）
- `cryptography` 库当前未在 `token.py` 中直接调用，预留给 v1 PKI 模块
- `ActionGuard` 依赖 `AuditLog` 接口注入，不直接 import 具体存储实现

## 升级与停更预案
- stdlib `hmac`：随 Python 版本维护，无停更风险；若 v1 切换到非对称签名，仅需修改 `token.py` 并引入 `cryptography`
- `cryptography`：由 PyCA 维护，停更概率极低；引入时只需修改 `token.py`
- OPA 切换：届时实现 `OPAClassifier(RiskClassifier)` 替换 `CodeClassifier`，接口不变
