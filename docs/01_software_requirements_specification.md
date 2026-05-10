# Action-Oriented Agentic Tutor 软件需求规格说明

## 1. 背景与目标

本项目来自课程小组作业 “Build an Action-Oriented Agentic Tutor with SWE-Agent”。作业要求使用 SWE-Agent 或其他 AI coding tools 构建一个行动导向的智能导师原型。

该 Tutor 的核心目标不是讲授知识、解释概念或直接给答案，而是基于学生的学习轨迹识别浅层理解、回避主题或随时间衰退的知识点，并生成具体、可执行的学习提醒，推动学生进行主动思考或练习。

本项目应同时产出可演示的软件原型、prompt log、报告材料和 3 分钟 demo 视频素材。

## 2. 产品定位

### 2.1 产品名称

Action-Oriented Agentic Tutor

### 2.2 一句话描述

一个接收任意形式学习资料或链接，将非结构化输入建模为学习轨迹索引，检测学习缺口，并生成行动导向学习 nudges 的轻量 Web 应用。

### 2.3 核心原则

- 不直接讲课。
- 不给最终答案。
- 不提供完整解题过程。
- 输出必须推动学生做一件具体的学习动作。
- 输出应针对学生的学习轨迹，而不是泛泛而谈。
- 系统应能展示从学习轨迹到弱点识别再到 nudge 生成的处理链路。

## 3. 用户与使用场景

### 3.1 主要用户

- 学生：上传或输入自己的学习记录，并接收下一步行动建议。
- 教师 / 助教：查看系统如何从学习轨迹中判断学生的薄弱点。
- 课程评审者：通过 demo 理解 SWE-Agent 参与构建的过程、原型能力与局限。

### 3.2 典型场景

1. 学生在 Web 页面中粘贴任意学习材料、上传资料，或输入相关链接。
2. 系统通过解析器、LLM API、RAG 等方式理解非结构化输入，抽取学习事件、概念、证据和时间线。
3. 系统形成可被程序处理的结构化学习轨迹索引。
4. 系统识别薄弱、回避或已经衰退的概念。
5. 系统输出一个或多个短小、直接、可执行的 nudges。
6. 用户可以查看系统的分析过程摘要，用于验证原型逻辑。

## 4. 输入与输出需求

### 4.1 输入数据

系统输入应以开放式、非结构化资料为主，而不是要求用户手动准备结构化 JSON。轻量 Web 应用至少应支持文本输入和示例资料加载，建议逐步支持文件上传和链接读取。

输入内容可以是：

- 任意文本：学习笔记、复习总结、聊天记录、教师反馈、错题反思。
- 学习资料：Markdown、TXT、PDF、Word 文档、CSV 练习日志等。
- 链接：课程页面、在线笔记、练习记录页面、题目页面、公开学习资源链接。
- 半结构化记录：表格、列表、错题本、时间线日志。
- 原始 JSON：作为调试、测试和 demo 的备用输入格式。

系统应允许资料中缺失部分字段，例如没有明确时间戳、没有分数、没有概念标签。Trace Indexer 需要尽可能抽取可用信号，并对不确定字段标注置信度或缺失状态。

### 4.2 输入摄取与规范化

Trace Indexer 前应包含 input ingestion 能力，用于将不同输入来源统一成可处理文本和元数据：

- 文本框输入：直接读取用户粘贴内容。
- 文件上传：提取文件正文、文件名、页码或行号等来源信息。
- 链接输入：抓取或读取链接内容，并保留 URL、标题、抓取时间。
- 示例数据：内置 2 到 3 个非结构化学生资料案例，便于稳定 demo。

规范化后的内部输入建议包含：

```json
{
  "source_id": "upload_001",
  "source_type": "text | file | url | example",
  "title": "Recursion practice notes",
  "raw_content": "I kept forgetting the base case in recursion exercises...",
  "metadata": {
    "url": null,
    "filename": null,
    "captured_at": "2026-05-10T14:30:00+08:00"
  }
}
```

### 4.3 Trace Indexer 目标结构

非结构化资料需要被 Trace Indexer 建模为结构化学习轨迹。该结构是后续 Gap Detector 和 Nudge Engine 的主要输入。

```json
{
  "student_id": "student_001",
  "course": "Intro to Algorithms",
  "trace": [
    {
      "timestamp": "2026-05-01T20:30:00+08:00",
      "type": "exercise",
      "concepts": ["recursion", "base case"],
      "summary": "Solved recursion exercises, failed two base-case questions.",
      "score": 0.55,
      "errors": ["missing base case", "wrong stopping condition"],
      "confidence": 0.4
    }
  ]
}
```

### 4.4 输出数据

系统输出应包含：

- 被识别出的学习缺口。
- 缺口类型：weak、avoided、decaying 等。
- 支撑证据：来自学习轨迹的简短依据。
- 行动导向 nudge。
- 可选：建议练习时长、优先级、下一次复习时间。

示例输出：

```json
{
  "target_concept": "base case in recursion",
  "gap_type": "weak",
  "evidence": "Recent exercise logs show repeated missing base-case errors.",
  "nudge": "Write three recursive functions and mark the exact line where recursion must stop before running the code.",
  "priority": "high"
}
```

## 5. 功能需求

### FR-1 Trace Indexer

系统必须包含 Trace Indexer，用于解析、理解并索引学生学习历史。Trace Indexer 是本项目的关键智能组件，应承担从非结构化资料到结构化学习轨迹的建模工作。

具体需求：

- 支持读取文本、文件内容、链接内容、半结构化日志和原始 JSON。
- 使用规则解析、LLM API、embedding、RAG 或其组合，将输入转成内部结构化记录。
- 从资料中抽取概念、时间、记录类型、表现指标、错误信息、情绪或信心线索、证据片段。
- 对抽取结果保留来源引用，例如文本片段、文件页码、URL 或行号。
- 对 LLM 抽取结果进行 schema validation，避免输出不可被程序处理的自由文本。
- 对不确定字段记录 confidence，供后续分析降权使用。
- 按概念聚合学习事件。
- 输出可被 Gap Detector 使用的索引结构。

验收标准：

- 给定一段非结构化学习资料，系统能抽取至少 3 条结构化 learning events。
- 给定一个链接或上传资料，系统能展示资料被解析后的文本摘要和来源信息。
- 系统能列出涉及的概念，并按概念展示相关事件数量、最近学习时间、平均表现、错误摘要或证据片段。
- 即使输入资料不完整，系统也能产出部分结构化结果，并标注缺失字段或置信度。

### FR-2 Gap Detector

系统必须包含 Gap Detector，用于识别薄弱、回避或衰退概念。

具体需求：

- 识别 weak concept：低分、低信心、多次错误或错误类型重复。
- 识别 avoided concept：长时间没有练习，但在学习目标中出现过或曾经表现较差。
- 识别 decaying concept：过去表现较好，但最近长期未复习或近期表现下降。
- 为每个 gap 生成简短证据。
- 为 gap 排序，优先展示最值得行动的 1 到 3 个问题。

验收标准：

- 系统能对示例数据输出至少一个 gap。
- gap 类型与示例数据中的表现模式基本一致。
- 输出包含 evidence，而不是只给结论。

### FR-3 Nudge Engine

系统必须包含 Nudge Engine，用于生成直接、可执行的行动提示。

具体需求：

- 根据 Gap Detector 输出生成 nudge。
- nudge 必须简短、明确、行动导向。
- nudge 不应包含完整知识解释、答案或解题过程。
- nudge 应要求学生进行某种动作，例如写、画、预测、比较、改错、重新尝试、限时练习。
- 对不同 gap 类型使用不同策略。

验收标准：

- 对每个 gap 至少生成一个 nudge。
- nudge 中包含明确动词。
- nudge 不直接给答案。
- nudge 不超过 2 句话。

### FR-4 Guided Interaction

系统建议支持简单的引导式交互。

具体需求：

- 当输入信息不足时，系统询问补充问题，例如课程主题、学习目标、近期练习情况。
- 用户可以选择示例非结构化资料快速演示。
- 用户可以修改或重新生成 nudge。

验收标准：

- 用户可以从空白状态进入一次完整演示流程。
- 用户不需要手动构造复杂数据也能看到系统效果。

### FR-5 Evaluation View

系统建议提供一个评估或调试视图，支持课程报告与 demo。

具体需求：

- 展示 Trace Indexer 的解析结果。
- 展示原始输入如何被整理为结构化 learning events。
- 展示 RAG/LLM 抽取的证据片段和置信度。
- 展示 Gap Detector 的判断结果。
- 展示 Nudge Engine 的最终输出。
- 允许保存或复制一次运行结果，用于报告和 prompt log。

验收标准：

- demo 中可以清楚展示三大组件的处理链路。
- 评审者可以看出系统不是简单聊天机器人，而是有明确模块设计。

## 6. 非功能需求

### NFR-1 可演示性

原型必须支持 3 分钟视频演示。推荐流程为：

1. 在 Web 页面加载一份非结构化示例资料或输入链接。
2. 展示资料摄取和 Trace Indexer 的结构化结果。
3. 展示识别出的 gap。
4. 展示行动导向 nudge。
5. 简要展示 prompt log 或开发过程反思。

### NFR-2 可解释性

系统应展示关键中间结果，便于说明设计逻辑和评估系统质量。

### NFR-3 低实现复杂度

考虑课程作业性质，优先实现可运行、可解释、可演示的轻量 Web 原型，而不是追求完整生产系统。LLM/RAG 能力可以先以小规模资料、简单向量检索和固定 schema 抽取实现。

### NFR-4 可扩展性

系统设计应允许后续加入：

- RAG 检索。
- 向量索引。
- 更多学习数据源。
- 多轮学生交互。
- 长期学习画像。

### NFR-5 隐私与安全

如果使用真实学生数据，应避免包含姓名、学号、联系方式等敏感信息。原型演示推荐使用虚构数据。

若调用 LLM API，API key 不应暴露在前端代码中。推荐通过轻量后端代理调用模型服务，并在报告中披露 AI 服务的使用范围。

### NFR-6 Web 应用形态

最终展现格式必须是轻量化 Web 应用。用户应通过浏览器完成资料输入、分析触发、结构化结果查看和 nudge 查看。

## 7. 建议系统架构

```mermaid
flowchart LR
    A["Web Input: Text / File / URL"] --> B["Input Ingestion"]
    B --> C["Raw Content + Metadata"]
    C --> D["Trace Indexer: LLM / RAG / Parser"]
    D --> E["Structured Learning Events"]
    E --> F["Concept Trace Index"]
    F --> G["Gap Detector"]
    G --> H["Ranked Learning Gaps"]
    H --> I["Nudge Engine"]
    I --> J["Action-Oriented Nudges"]
    E --> K["Evaluation / Debug View"]
    F --> K
    G --> K
    I --> K
```

### 7.1 Structured Learning Event 输出结构

```json
{
  "event_id": "event_001",
  "timestamp": "2026-05-01T20:30:00+08:00",
  "type": "exercise | note | error | feedback | reflection",
  "concepts": ["recursion", "base case"],
  "summary": "The student repeatedly missed the stopping condition in recursion exercises.",
  "performance": {
    "score": 0.55,
    "confidence": 0.4,
    "attempts": 3
  },
  "errors": ["missing base case", "wrong stopping condition"],
  "evidence": [
    {
      "source_id": "upload_001",
      "quote": "I failed two recursion questions because I forgot when to stop.",
      "location": "paragraph 2"
    }
  ],
  "extraction_confidence": 0.82
}
```

### 7.2 Concept Index 输出结构

```json
{
  "concept_index": {
    "recursion": {
      "events": 4,
      "last_seen": "2026-05-01T20:30:00+08:00",
      "average_score": 0.58,
      "average_confidence": 0.42,
      "common_errors": ["missing base case"],
      "evidence_sources": ["upload_001:paragraph 2"]
    }
  }
}
```

### 7.3 Gap Detector 输出结构

```json
{
  "concept": "recursion",
  "gap_type": "weak",
  "severity": 0.82,
  "evidence": [
    "Average score below 0.6",
    "Repeated missing base-case error"
  ]
}
```

### 7.4 Nudge Engine 输出结构

```json
{
  "concept": "recursion",
  "nudge": "Before solving another recursion problem, write the stopping condition first and test it with the smallest input.",
  "action_type": "write-and-test",
  "priority": "high"
}
```

## 8. 原型范围

### 8.1 MVP 必须完成

- 一个可以运行的本地原型。
- 最终形态为轻量 Web 应用。
- 支持粘贴任意文本资料和加载非结构化示例资料。
- Trace Indexer 能调用 LLM API 或使用模拟 LLM/RAG pipeline，将非结构化输入整理成结构化 learning events。
- 实现 Trace Indexer、Gap Detector、Nudge Engine 三个模块。
- 展示至少一个完整处理结果。
- 生成 prompt log 和报告素材。

### 8.2 可选增强

- 多个示例学生画像。
- 支持 PDF、Word、CSV 或 Markdown 学习资料。
- 支持 URL 内容抓取和网页正文抽取。
- 支持真实 embedding 检索和 RAG evidence retrieval。
- 支持 LLM 生成更自然的 nudges。
- 支持导出结果为 JSON 或 Markdown。

### 8.3 明确不做

- 不实现完整 LMS 系统。
- 不接入真实学生账号。
- 不需要生产级权限系统。
- 不需要真实部署到云端。
- 不需要构建完整 DeepTutor 复刻系统。
- 不要求对所有网站链接都能稳定抓取；原型可对链接抓取失败提供手动粘贴替代路径。

## 9. 质量评价标准

### 9.1 功能评价

- 三个 required components 是否真实存在。
- 输入、处理、输出链路是否完整。
- 非结构化输入是否能被整理为结构化学习轨迹。
- nudge 是否行动导向。
- 是否避免直接讲解和给答案。

### 9.2 工程评价

- 代码结构是否清晰。
- 模块边界是否符合需求。
- 示例数据是否可复现。
- demo 是否稳定。

### 9.3 课程评价

- 是否体现 SWE-Agent 或 AI coding tools 的使用过程。
- 是否记录 prompt log。
- 是否能分析 SWE-Agent 的能力与局限。
- 是否能诚实说明失败尝试和改进空间。

## 10. 验收用例

### AC-1 基础完整流程

给定一份非结构化示例学习资料，系统应完成：

1. 解析输入。
2. 抽取结构化 learning events。
3. 建立概念索引。
4. 检测至少一个 gap。
5. 输出至少一个 nudge。

### AC-1B 链接或资料输入

给定一个学习资料链接或上传文件，系统应尝试读取资料内容；如果读取失败，应提示用户粘贴文本内容作为替代输入。

### AC-2 避免直接答案

给定一个包含错误题目的学习记录，系统输出应引导学生重新尝试或反思，而不是给出题目答案。

### AC-3 衰退概念识别

给定某概念过去分数较高但长期没有复习的记录，系统应能将其标记为 decaying 或 needs review。

### AC-4 Demo 可用性

运行原型后，用户应能在 3 分钟内看懂：

- 输入是什么。
- 系统做了什么分析。
- 最终 nudge 是什么。
- 这个原型如何对应作业要求。

## 11. 交付物映射

| 作业交付物 | 软件项目内对应产物 |
| --- | --- |
| Working or failed prototype | 本地可运行原型代码与示例数据 |
| Prompt log | `docs/prompt_log.md` |
| Report <= 4 pages | `docs/report_outline.md` 或最终 PDF/Docx |
| 3 min demo video | 以 MVP 流程录屏 |

## 12. 风险与应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| SWE-Agent 生成代码不稳定 | 原型无法按预期运行 | 保留手动修复记录，写入反思 |
| nudge 变成讲解 | 不符合任务核心 | 设置明确的输出约束和测试用例 |
| 输入数据太自由 | 解析复杂度上升 | MVP 先支持文本粘贴、内置示例和 schema-constrained LLM 抽取 |
| 链接抓取不稳定 | demo 中断 | 准备链接内容缓存和手动粘贴替代路径 |
| LLM 输出格式漂移 | 后续程序无法处理 | 使用 JSON schema、校验和 fallback parser |
| API key 泄露 | 安全风险 | 使用后端代理和环境变量，不在前端暴露 key |
| 原型功能太大 | 无法按时完成 | 优先三组件链路和 demo 稳定性 |
| 缺少真实评估 | 报告说服力不足 | 使用 2 到 3 个虚构学生案例做定性评估 |
