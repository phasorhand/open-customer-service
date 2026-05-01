# Skills Repo · OSS 调研

## 目标
实现 bundled Skills Repo：从本地 SKILL.md 文件目录加载技能，按关键词匹配客户消息，将匹配的技能文本注入 LLM 提示词，使 CS Reply Agent 能遵循标准化服务流程。

## 候选对比

| 候选 | License | 最近 commit | Stars | 体量 | 评分 | 备注 |
|---|---|---|---|---|---|---|
| Anthropic Claude Skills 规范 | — | — | — | — | ⚠️ 借抽象 | §6.6 B类：借 frontmatter + Markdown 目录结构思路 |
| OpenHands AgentSkills | Apache-2.0 | 2026-03 | 40k | 重 | ❌ | 专为软件工程任务，语义不匹配；体量过重 |
| [python-frontmatter](https://github.com/eyeseast/python-frontmatter) | MIT | 2025-11 | 900 | ~40KB | ✅ 复用 | 解析 SKILL.md 的 YAML frontmatter；轻量，社区维护 |
| [mistune](https://github.com/lepture/mistune) | BSD-3 | 2026-01 | 2.4k | ~200KB | ❌ | Markdown 渲染；MVP 只需读 body 文本，不需要 HTML 渲染 |

## 决策
- **复用**：`python-frontmatter @ ^1.1` —— 解析 SKILL.md 的 YAML frontmatter（name / description / keywords）；body 是技能文本
- **自建**：`SkillRepo` —— 目录扫描 + 关键词匹配逻辑（< 100 行）；产品差异化（§6.6 C 类）

## 集成边界
- `python-frontmatter` 仅在 `skill_repo.py` 内使用
- `SkillRepo` 暴露 `match(text: str) → list[str]`（技能 body 列表）给 Worker
- bundled 技能目录结构：`skills/bundled/<name>/SKILL.md`

## 升级与停更预案
- python-frontmatter 若停更：fronmatter 格式简单，可用 `re` 自解析 `---` 区块（~20 行）
- 语义检索（v1）：实现 `SemanticSkillRepo` 满足同一接口，构造时替换
