# GPT × Codex 项目协作模板

这套模板用于以下工作流：

**ChatGPT 网页版负责思考与方案 → GitHub 保存项目上下文 → Codex 负责实现 → GitHub 回写状态 → ChatGPT 继续分析。**

## 目录结构

```text
.
├── AGENTS.md
├── README.md
└── docs/
    ├── CONTEXT.md
    ├── DECISIONS.md
    └── STATUS.md
```

## 推荐使用方式

### 1. 在 ChatGPT 网页版讨论方案

讨论完成后，让 ChatGPT 将最终结论整理为：

- `docs/CONTEXT.md`：当前需求、目标、约束、设计方案
- `docs/DECISIONS.md`：已经确定的重要决策及原因

不要把长篇聊天记录直接交给 Codex，只同步最终有效结论。

### 2. 在 Codex 开始执行

推荐开场指令：

> 先阅读 AGENTS.md、docs/CONTEXT.md、docs/DECISIONS.md、docs/STATUS.md，理解项目目标、约束、已确认决策和当前开发状态。然后执行 CONTEXT.md 中最新的待实现需求。完成后自测，并更新 docs/STATUS.md。

### 3. Codex 完成后

Codex 应更新：

- 本次完成内容
- 修改文件
- 当前实现状态
- 已知问题
- 待完成事项
- 下一步建议

然后提交到 GitHub。

### 4. 回到 ChatGPT 网页版

让 ChatGPT 阅读 GitHub 中最新的：

- `docs/STATUS.md`
- `docs/CONTEXT.md`
- `docs/DECISIONS.md`
- 必要的代码文件

再继续讨论下一轮方案。

---

## 最小协作闭环

```text
ChatGPT
  ↓
CONTEXT / DECISIONS
  ↓
GitHub
  ↓
Codex
  ↓
代码 + STATUS
  ↓
GitHub
  ↓
ChatGPT
```

原则：**聊天记录不是项目记忆，仓库文件才是。**
