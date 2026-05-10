# Action-Oriented Agentic Tutor 原型实现计划

## 1. 实现策略

根据作业要求，原型应优先证明三件事：

1. 系统能读取并结构化学生学习轨迹。
2. 系统能基于轨迹识别学习缺口。
3. 系统能生成不讲解、不直接给答案、行动导向的 nudge。

因此原型固定采用轻量 Web 应用形态。用户在浏览器中输入任意文本、上传资料或填写链接，系统在后台完成资料摄取、LLM/RAG 结构化建模、gap detection 和 nudge generation。

## 2. 推荐技术方案

### 方案 A：轻量 Web App + 本地规则/模拟 LLM Pipeline

适合快速稳定演示。

- 前端：HTML/CSS/JavaScript 或 React/Vite
- 后端：可选，MVP 可先用本地 mock LLM extraction
- 数据：内置非结构化文本示例
- 算法：规则解析 + schema validation + gap detection

优点：

- Demo 直观。
- 容易展示三大组件。
- 便于截图和录屏。
- 不依赖外部 API，稳定性高。

缺点：

- Trace Indexer 的智能能力展示有限，需要在报告中说明可替换为真实 LLM API。

### 方案 B：轻量 Web App + LLM API / RAG Backend

适合更贴近作业主题和真实应用。

- 前端：React/Vite 或原生 HTML/CSS/JS。
- 后端：Node/Express 或 Python/FastAPI。
- LLM：通过后端调用 LLM API，将非结构化输入抽取为 JSON schema。
- RAG：对输入资料切片、embedding、检索相关证据片段，再交给抽取与分析模块。
- 数据：本地内存或 JSON 文件即可。

优点：

- Trace Indexer 能体现 LLM API、RAG 和 schema-constrained extraction。
- 更符合“任意资料或链接输入”的产品目标。

缺点：

- 需要 API key、后端代理和错误处理。
- 网络/API 不稳定时会影响 demo。

### 推荐选择

建议采用折中方案：轻量 Web App + 后端抽象接口。开发时先实现 mock extraction，保证 demo 稳定；再预留真实 LLM API/RAG adapter。这样即使 API 不可用，系统也能演示完整链路；如果 API 可用，则 Trace Indexer 可以展示真实的非结构化资料建模能力。

## 3. 模块拆分

### 3.1 Trace Indexer

输入：

- 用户输入的任意文本。
- 上传资料解析后的文本。
- 链接抓取后的网页正文。
- 示例非结构化学习资料。

输出：

- structured learning events。
- concept index。

核心逻辑：

- Input ingestion：识别输入来源，读取 raw content 和 metadata。
- Chunking：将长文本切分成可检索片段。
- Retrieval：根据学习目标或候选概念检索相关 evidence chunks。
- LLM extraction：调用 LLM API，按固定 JSON schema 抽取学习事件。
- Schema validation：校验 LLM 输出，缺失字段填 null，并记录 confidence。
- Fallback parsing：当 LLM 不可用时，使用规则和内置示例生成结构化事件。
- 以 concept 为 key 聚合事件。
- 统计最近出现时间、平均分、平均信心、错误频次。

### 3.2 Gap Detector

输入：

- concept index。

输出：

- ranked gaps。

核心逻辑：

- score 低于阈值，标记为 weak。
- confidence 低于阈值，增加 severity。
- 错误重复出现，增加 severity。
- 距今天较久未复习，标记为 decaying。
- 出现过但练习次数少或近期没有练习，标记为 avoided。

### 3.3 Nudge Engine

输入：

- ranked gaps。

输出：

- nudges。

核心逻辑：

- weak：要求学生重做、对比、定位错误。
- avoided：要求学生进行短时间启动练习。
- decaying：要求学生快速回忆、检索练习或限时复盘。
- 输出限制：最多两句话，不给答案，不解释概念。

## 4. 数据样例设计

建议准备 3 个学生案例：

### Case 1：弱概念

学生多次在 recursion 的 base case 上出错，分数和信心都低。

示例输入形态：

- 一段学生反思文本。
- 一段错题日志。
- 一个模拟课程练习页面链接。

预期输出：

- gap type: weak
- nudge: 要求学生先写停止条件，再测试最小输入。

### Case 2：回避概念

学生长期没有练习 dynamic programming，但课程目标中多次出现。

示例输入形态：

- 一份课程学习计划。
- 一段学生复习记录，显示其跳过 dynamic programming。

预期输出：

- gap type: avoided
- nudge: 要求学生用 10 分钟写出状态定义和转移，不需要完成整题。

### Case 3：衰退概念

学生之前掌握 binary search，但最近三周未复习。

示例输入形态：

- 一份按日期排列的学习日志。
- 一段旧测验反馈加近期空白记录。

预期输出：

- gap type: decaying
- nudge: 要求学生不看笔记写出边界更新规则，并用两个测试输入检查。

## 5. 页面或界面设计

Web UI 建议包含以下区域：

- 左侧：资料输入区，包含文本框、文件上传、URL 输入和示例选择。
- 中间：Trace Indexer 结果，展示 extracted events、concept index、evidence snippets、confidence。
- 右侧：Gap Detector 与 Nudge Engine 输出。
- 底部：运行日志或导出结果。

核心操作按钮：

- Load Example
- Parse Source
- Analyze Trace
- Regenerate Nudge
- Export Result

## 6. 开发任务清单

### Milestone 1：项目骨架

- 创建原型项目结构。
- 准备轻量 Web 应用。
- 准备非结构化示例资料。
- 准备基础运行方式。

完成标准：

- 项目可以启动。
- 用户可以在 Web 页面看到输入区和示例资料。

### Milestone 2：资料摄取与 Trace Indexer

- 实现文本输入读取。
- 实现示例资料加载。
- 预留文件上传和 URL 输入接口。
- 实现 LLM/RAG adapter 抽象。
- 实现 mock extraction 或真实 LLM schema extraction。
- 实现 Trace Indexer。

完成标准：

- 非结构化文本能被整理为 structured learning events。
- 页面能展示抽取证据和 confidence。

### Milestone 3：Gap 与 Nudge 核心逻辑

- 实现 Gap Detector。
- 实现 Nudge Engine。
- 添加基础测试或示例运行结果。

完成标准：

- 示例数据能跑出完整结果。
- 输出中包含 concept index、gaps、nudges。

### Milestone 4：演示界面

- 实现输入区域。
- 实现资料解析结果展示。
- 实现分析结果展示。
- 实现 nudge 展示。
- 加入示例切换。

完成标准：

- 可以完成 3 分钟 demo 流程。

### Milestone 5：课程交付材料

- 整理 prompt log。
- 整理报告大纲。
- 截图或录屏 demo。
- 总结 SWE-Agent 能力与局限。

完成标准：

- 所有作业交付物均有对应文件或素材。

## 7. Prompt Log 模板

后续与 SWE-Agent 或 AI coding tools 交互时，应记录：

```markdown
## Prompt 1

### Goal
希望 AI 完成什么任务。

### Prompt
实际输入给 AI 的 prompt。

### Output Summary
AI 生成了什么。

### Result
是否成功，是否需要人工修改。

### Reflection
这个 prompt 暴露了什么能力或局限。
```

## 8. 报告结构建议

报告限制为 4 页以内，建议结构如下：

1. Introduction
   - 作业目标。
   - SWE-Agent 或 AI coding tools 简介。
2. System Design
   - 三个核心组件。
   - 非结构化输入到结构化 learning events 的 Trace Indexer 设计。
   - LLM API/RAG 在 Trace Indexer 中的作用。
   - 数据流与架构图。
3. Prototype and Evaluation
   - 非结构化示例输入。
   - 输出结果。
   - nudge 是否符合行动导向原则。
4. SWE-Agent Reflection
   - 能力。
   - 局限。
   - 失败尝试。
   - 惊喜发现。
5. Feasibility and AI Usage Disclosure
   - 转化为真实应用的可行性。
   - AI 工具使用说明。

## 9. Demo 脚本建议

3 分钟 demo 可以按如下节奏：

- 0:00-0:30：说明目标，强调 Tutor 不讲解、不直接给答案。
- 0:30-1:00：展示任意文本、资料或链接输入。
- 1:00-1:35：点击 Parse/Analyze，展示 Trace Indexer 如何把非结构化资料整理成 structured events 和 concept index。
- 1:35-2:20：展示 Gap Detector 与 Nudge Engine 输出，并解释为什么它是行动导向。
- 2:20-3:00：展示 prompt log 或反思，说明 SWE-Agent 的作用和局限。

## 10. 最小可行验收

只要满足以下条件，就可以作为 working prototype 提交：

- 能运行。
- 是轻量 Web 应用。
- 能加载至少一个非结构化学习资料样例。
- 能将非结构化资料整理成 structured learning events。
- 能展示三个组件的输出。
- 能生成至少一个合格 nudge。
- 有 prompt log。
- 报告能说明设计、评估、能力与局限。

## 11. 实际实现状态

截至最终整理文档时，原型已完成以下内容：

- 前端采用 React + Vite + TypeScript。
- 后端采用 FastAPI + Pydantic。
- Python 环境通过 `uv` 和项目内 `.venv` 管理，不使用系统 Python。
- Trace Indexer 接入真实 OpenAI-compatible LLM API。
- Embedding API 与 LLM API 分离配置，支持不同服务商。
- Chroma 持久化向量库用于 RAG evidence chunk indexing。
- 输入支持统一文本框、文件上传、文本中的 URL 自动读取和内置示例加载。
- 前端支持中文/英文语言选项。
- 输入区支持 Markdown 编辑/预览切换。
- 右侧结果区在生成时展示 AI 处理过程，生成完成后自动隐藏。
- 学习建议使用分页卡片展示，避免长结果撑高页面。
- Debug 模式可查看 Trace Indexer、Gap Detector 和 Nudge Engine 的结构化输出。
- 三个中文测试案例已经替换为更真实的学生学习日志、平台导出表和本地反馈页面。

最终验证方式：

```bash
uv --cache-dir .uv-cache run pytest
npm run build
```

最近一次验证结果：

- 后端测试：12 passed。
- 前端构建：成功。

## 12. 已知限制

- 真实 LLM/embedding API 调用可能较慢，当前前端通过分步进度缓解等待感，但还没有实现后台任务队列或流式输出。
- URL 抓取只适合可公开访问且正文结构较简单的页面。
- PDF 解析为第一版基础能力，复杂排版或扫描件不保证准确。
- Gap Detector 仍是启发式算法，适合 demo 和课程原型，不应直接作为高风险教学判断依据。
- Nudge Engine 通过 prompt 和 guardrail 控制输出，但仍需要人工或后续用户反馈机制评估教学质量。
