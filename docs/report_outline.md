# Report Outline

> 课程报告限制为 4 页以内。本大纲与 `03_final_report.md` 保持一致，重点放在 SWE-Agent 使用分析、软件设计 rationale、evaluation 和反思，不展开部署或具体技术排障。

## 1. Introduction

- 介绍 Action-Oriented Agentic Tutor 的目标。
- 说明系统接收开放式学习轨迹资料。
- 强调 tutor 不讲完整知识点、不直接给答案，而是生成可执行的下一步学习动作。

## 2. Introduction To The SWE-Agent Employed

- 说明本项目使用 Codex 作为 SWE-Agent-style AI coding agent。
- 说明它参与了需求分析、规划、实现、迭代、文档和报告整理。
- 强调交互方式是人类持续审查和引导，agent 负责快速实现与修改。

## 3. Design Rationale

- Trace Indexer：把非结构化学习资料变成 structured learning events。
- Gap Detector：识别 weak、avoided、decaying concepts。
- Nudge Engine：生成行动导向建议。
- 说明为什么系统不能只是一个普通聊天机器人，而需要可检查的中间结构。
- 说明为什么“是否给例题”应由 LLM 根据学习轨迹判断，而不是写成代码硬约束。

## 4. Prototype

- 轻量 Web 应用。
- 统一输入框支持文本、Markdown、链接和附件。
- 中文真实测试案例。
- Debug view 支持查看 Trace Indexer、Gap Detector、Nudge Engine 输出。
- 最终建议分页展示。

## 5. Evaluation

- 定性评估是否完成从 raw learning trace 到 structured events、gaps、nudges 的流程。
- 检查 nudge 是否行动导向、是否避免完整答案。
- 检查 UI 是否支持 demo：进度可见、完成后聚焦结果、长结果不撑开页面。
- 使用三个中文学习案例进行评估。

## 6. Capability And Limits Of SWE-Agent

### Capabilities

- 能快速把模糊需求转为工程结构。
- 能跨前后端协调修改 schema、API、UI 和测试。
- 能在多轮反馈后快速迭代原型。
- 能整理 prompt log 和报告材料。

### Limitations

- 容易先给出形式正确但产品判断不够细的实现。
- 对教育场景中的“合适建议”理解有限，需要人类把关。
- 初始测试数据可能偏开发者视角，不一定像真实学生输入。
- UI 体验需要用户明确指出后才逐步改善。

## 7. Analytics And Reflection

必须回答：

- Capabilities And Limitations Observed.
- What We Or The SWE-Agent Tried That Did Not Work.
- What Surprised Us.
- Feasibility Of Turning The Prototype Into A Real Application.

反思重点：

- SWE coding agent 的使用心得；
- 人类如何纠正 agent 的产品理解；
- 软件设计中的错误方向和修正；
- 原型转真实应用的教学、隐私和评估挑战。
- Codex 能够检查浏览器界面、读取终端日志并自动定位实现问题后，人类角色如何从代码细节转向架构设计与开发规划。

不要在报告主体展开：

- 本机环境错误；
- 依赖安装细节；
- 具体 API 报错；
- 低层技术排障日志。

## 8. AI Usage Disclosure

- 说明使用 Codex 辅助完成哪些工作。
- 说明用户审核和调整了哪些关键方向。
- 说明最终结果是人类判断与 AI coding agent 协作完成。
