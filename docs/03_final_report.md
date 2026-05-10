# Action-Oriented Agentic Tutor Final Report

## 1. Introduction

This project builds a lightweight prototype of an Action-Oriented Agentic Tutor. The tutor accepts open-ended learning traces, such as study notes, exercise logs, teacher feedback, files, and links. It then turns these unstructured materials into structured learning events, detects possible learning gaps, and generates short, actionable learning suggestions.

The purpose of the tutor is not to lecture the student, provide full explanations, or give final answers. Instead, it should help the student take the next useful learning action. For example, if a student repeatedly fails recursion problems because the base case is missing, the tutor should guide the student to write the smallest input and stopping condition before attempting the recursive call.

The final prototype is a lightweight Web application with three conceptual modules:

- Trace Indexer: organizes unstructured learning materials into structured events and concept evidence.
- Gap Detector: identifies weak, avoided, or decaying concepts.
- Nudge Engine: generates immediately actionable learning suggestions.

The project also includes a prompt log, realistic Chinese test cases, and documentation of how a SWE-Agent-style coding agent was used during development.

## 2. Introduction To The SWE-Agent Employed

In this project, Codex was used as a SWE-Agent-style AI coding agent. It was not used only as a code autocomplete tool. Instead, it participated across the full software development process:

- reading the local assignment brief and extracting requirements;
- translating the assignment into software requirements and implementation plans;
- proposing the system architecture;
- implementing the frontend, backend, data models, analysis pipeline, tests, and documentation;
- revising the prototype according to user feedback;
- helping diagnose design and interaction problems;
- producing the prompt log and final report drafts.

The interaction pattern was iterative. The user first asked Codex to understand the assignment and create requirements. Then the user refined the product direction, for example requiring arbitrary text/file/link input, LLM/RAG-based Trace Indexer behavior, a lightweight Web UI, Chinese language support, concrete practice suggestions, realistic test data, and a cleaner result interface. Codex made implementation changes after each feedback round.

This process resembled a collaborative software engineering workflow: the agent proposed and implemented, while the user reviewed whether the result matched the educational purpose and adjusted the direction when needed.

## 3. Design Rationale

The design is based on the idea that an action-oriented tutor needs an explicit analysis pipeline rather than a single chat response. A generic chatbot could read a student note and respond with advice, but it would be difficult to inspect why the advice was generated. Therefore, the prototype separates the system into three modules.

### 3.1 Trace Indexer

The Trace Indexer is responsible for converting open-ended learning materials into structured learning data. It handles text, file content, URLs found in the input, and built-in examples. The output includes learning events, concepts, errors, evidence snippets, and concept-level summaries.

This module is important because the rest of the system depends on structured representations. Without the Trace Indexer, the tutor would only be reacting to raw text. With it, the system can reason over dates, topics, repeated mistakes, missing practice, and evidence.

### 3.2 Gap Detector

The Gap Detector identifies three types of learning gaps:

- Weak concepts: concepts with repeated mistakes or poor recent performance.
- Avoided concepts: concepts that appear in goals or course requirements but have few or no practice attempts.
- Decaying concepts: concepts that were previously understood but have not been practiced recently or show signs of hesitation.

This design mirrors the assignment's requirement that the tutor should identify shallow understanding, avoided topics, or knowledge that decays over time.

### 3.3 Nudge Engine

The Nudge Engine turns a learning gap into a concrete next step. A key design decision was that the tutor should not always force the output into a worksheet or exercise. Sometimes the right action is to attempt a small problem; sometimes it is to recall a rule, annotate an error, compare two cases, or restart from the first step of a problem.

Therefore, the final design asks the LLM to decide whether a concrete example problem is useful. If it is useful, the tutor should provide a specific starter exercise. If it is not, the tutor should still provide an immediately actionable learning step.

## 4. Prototype

The prototype is a lightweight Web application. The left side of the interface allows the user to enter learning trace materials in one unified input area. The input area supports Markdown preview so that realistic study logs, tables, links, and notes are easier to read. The user may also attach a file and load built-in Chinese test cases.

The right side presents the final learning suggestions. During analysis, it displays key stages of the AI process, such as organizing input materials, indexing learning traces, detecting learning gaps, and generating next actions. After the final answer is generated, this process view disappears so the user can focus on the result.

The final suggestions are displayed as paginated cards. This avoids a long vertical list when the tutor generates several detailed learning actions.

The prototype includes three realistic Chinese test cases:

1. A student repeatedly fails recursion problems because of missing or late base cases.
2. A student keeps avoiding dynamic programming even though it appears in the course checklist.
3. A student previously understood binary search but begins to forget boundary update rules after a long gap.

Each case includes a typed learning log, an attached Markdown file, and a linked local feedback page.

## 5. Evaluation

The prototype was evaluated qualitatively against the assignment goals.

First, the system can process open-ended learning traces instead of requiring the user to manually create structured JSON. This is important because real students are more likely to paste notes, logs, tables, or feedback than to prepare formal data.

Second, the system produces inspectable intermediate structures in debug mode. The user can see the Trace Indexer output, Gap Detector output, and Nudge Engine output. This supports evaluation because the tutor's response is not treated as a black box.

Third, the final suggestions are more action-oriented than a generic explanation. For example, the recursion case leads to steps such as identifying the smallest input, writing the stopping condition, and marking where the recursive call should happen. The dynamic programming case may lead to a small state-definition task rather than a full solution. The binary search case may ask the student to recover boundary rules from memory and test them on a small example.

Fourth, the interface was revised based on usability feedback. The user no longer sees three separate input boxes. The AI process is shown only while it is useful. Long results are paginated. Markdown learning logs are rendered instead of shown only as raw text.

Overall, the prototype satisfies the intended demonstration goal: it shows how an agentic tutor can move from raw learning traces to structured analysis and then to actionable learning guidance.

## 6. Capability And Limits Of The SWE-Agent Observed

### 6.1 Capabilities

Codex was effective at turning vague requirements into a working system. It could read the assignment, propose architecture, create documents, implement code across multiple files, and revise the prototype after feedback. It was especially useful for maintaining consistency across layers. For example, when a new nudge field was added, it updated backend schemas, service logic, frontend TypeScript types, and UI rendering together.

Codex was also effective at rapid iteration. The user could point out that the advice was too abstract, that the UI was too long, or that the test cases did not feel realistic, and Codex could translate that feedback into concrete software changes.

Another capability was documentation synthesis. Codex could reconstruct the development process into a prompt log and summarize design decisions, implementation outcomes, and reflections.

### 6.2 Limitations

The most important limitation was that Codex often optimized for a plausible implementation before fully understanding the educational nuance. For example, when asked to make suggestions more concrete, it initially moved toward making every suggestion include a specific exercise. That was technically clear but pedagogically too rigid.

Codex also tended to generate test data that looked structurally useful but not realistic enough. The first test cases contained developer-facing descriptions rather than authentic student records. Human review was needed to make the cases feel like real learning logs.

Another limitation was that Codex needed explicit feedback about UI priorities. It could build a functional interface quickly, but the first version was more like a technical demo. The final interface became better only after user feedback about unified input, result pagination, Markdown preview, and progress display.

These limitations suggest that SWE-Agent-style tools are powerful implementation accelerators but still need human direction for product judgment, pedagogy, and user experience.

## 7. Analytics And Reflection

### 7.1 Capabilities And Limitations Observed

The strongest capability observed was end-to-end engineering assistance. Codex could move from requirements to architecture, code, tests, and documentation. It was also good at making coordinated changes across the stack.

The main limitation was judgment. Codex could implement the literal request, but it did not always infer the deeper educational design intent. It needed the user to clarify when an implementation was too rigid, too abstract, or too developer-oriented.

### 7.2 What We Or The SWE-Agent Tried That Did Not Work

The first notable failed direction was making every learning suggestion contain a concrete exercise. This sounded useful, but it made the tutor less flexible. Some learning gaps are better addressed by recall, annotation, comparison, or restarting a partial attempt rather than by immediately assigning a new problem.

The second failed direction was using artificial test data. The initial examples described what the test case was supposed to contain instead of resembling what a student would actually paste. This weakened the credibility of the demo. The cases were later rewritten as Chinese learning logs with dates, problem names, mistakes, feedback, and exported activity tables.

The third issue was UI overexposure. Showing all generated suggestions at once made the result area too long. Keeping the AI process visible after completion also distracted from the final advice. Both were corrected through pagination and conditional progress display.

### 7.3 What Surprised Us

The most surprising observation was how far the coding agent could move beyond writing isolated code snippets. Codex could inspect the application state through the browser-facing workflow, reason from screenshots of the UI, read terminal and server logs, connect those observations back to the source code, and then patch the relevant frontend or backend files. This made the development process feel closer to an automated engineering loop than to a traditional code-completion interaction.

This changed the role of the human developer. Instead of manually tracing every bug or editing every implementation detail, the human increasingly focused on architecture, product direction, and development planning: what the tutor should do, what kind of user experience is acceptable, and what educational behavior is appropriate. Codex handled much of the lower-level implementation work, including locating files, reading logs, revising UI state logic, and updating related code paths.

Another surprise was that this automation did not remove the need for human judgment. It moved the bottleneck upward. The important decisions became less about how to write a specific function and more about whether the system design matched the tutoring goal. For example, the user still had to decide that advice should be actionable without forcing every suggestion into a question template.

### 7.4 Feasibility Of Turning The Prototype Into A Real Application

The prototype is feasible as the foundation for a real application, but several extensions would be necessary.

A real system would need richer integrations with learning management systems, online judges, note-taking tools, or course platforms. It would also need stronger privacy controls because learning traces may contain sensitive student information. The gap detection logic would need evaluation against real student outcomes, not only qualitative demo cases.

The tutor would also need a feedback loop. Students should be able to mark whether a suggestion was useful, too easy, too hard, or irrelevant. This feedback could improve future nudges and reduce overconfidence in automatically detected gaps.

In short, the prototype demonstrates feasibility, but a production system would require data governance, pedagogical validation, and longitudinal evaluation.

## 8. AI Usage Disclosure

Codex was used to assist with:

- assignment requirement analysis;
- requirements and planning documents;
- software architecture design;
- frontend and backend implementation;
- test case creation and revision;
- UI iteration;
- debugging and refinement;
- prompt log and report drafting.

The user reviewed and directed the main product decisions, including the requirement for open-ended input, separate LLM/embedding configuration, Chinese UI, realistic test data, optional exercise generation, paginated results, and Markdown preview.

The final prototype and documents should therefore be understood as a collaboration between human product judgment and SWE-Agent-style implementation support.
