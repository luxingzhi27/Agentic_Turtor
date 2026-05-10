import { type ReactNode, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  ClipboardList,
  Download,
  FileText,
  Languages,
  Loader2,
  Paperclip,
  Play,
  RefreshCcw,
  Settings2,
  Sparkles,
} from "lucide-react";
import { detectGaps, getExampleBundle, getExamples, getHealth, indexTrace, parseSource, regenerateNudges } from "./api";
import type { AnalysisResponse, ExampleInfo, HealthResponse, Nudge } from "./types";

type Language = "zh" | "en";
type ProcessStatus = "pending" | "active" | "done";
type ProcessItem = {
  title: string;
  detail: string;
  status: ProcessStatus;
};
type InputMode = "edit" | "preview";

const copy = {
  zh: {
    eyebrow: "行动导向智能导师",
    title: "输入学习轨迹，获得下一步练习行动。",
    inputTitle: "学习轨迹资料",
    inputHint: "在同一个输入框中粘贴笔记、错题记录、练习日志、教师反馈或链接。也可以附加一个文件。",
    edit: "编辑",
    preview: "预览",
    placeholder:
      "例如：\n2026-04-24 我做了 5 道递归题，只通过 2 道。factorial 忘记处理 n == 0，count_down 在 n = 0 后还继续递归。\n也可以直接粘贴课程页面链接：https://...",
    example: "载入测试资料",
    file: "附加文件",
    noFile: "未选择文件",
    analyze: "生成学习建议",
    analyzing: "分析中",
    progressTitle: "AI 处理过程",
    process: {
      parse: "整理输入资料",
      parseActive: "正在读取输入框、链接和附件，把资料合并成统一学习轨迹。",
      index: "建立学习轨迹索引",
      indexActive: "正在抽取学习事件、概念、证据片段，并写入检索索引。",
      gaps: "判断学习缺口",
      gapsActive: "正在比较近期表现、错误模式和缺失练习，排序薄弱/回避/衰退概念。",
      nudges: "生成下一步行动",
      nudgesActive: "正在生成可立即动手的建议；需要例题时会给出适合入手的具体题目。",
    },
    debug: "Debug 模式",
    resultTitle: "学习建议与练习步骤",
    emptyResult: "提交学习资料后，这里会直接显示可执行的学习建议。",
    priority: "优先级",
    action: "练习动作",
    exercise: "适合入手的例题",
    materials: "练习资料",
    steps: "建议步骤",
    checklist: "你需要产出",
    previous: "上一条",
    next: "下一条",
    advicePage: "建议",
    concept: "目标概念",
    regenerate: "重新生成建议",
    export: "导出结果",
    debugTitle: "调试信息",
    trace: "Trace Indexer 输出",
    gaps: "Gap Detector 输出",
    nudges: "Nudge Engine 输出",
    healthUnknown: "后端状态未知",
    ready: "服务已就绪",
    missing: "配置未完成",
    language: "语言",
    attachmentHelp: "支持 .txt、.md、.csv、.pdf",
  },
  en: {
    eyebrow: "Action-Oriented Agentic Tutor",
    title: "Turn learning traces into the next practice move.",
    inputTitle: "Learning Trace Materials",
    inputHint: "Paste notes, error logs, exercise history, feedback, or links in one box. You may attach one file too.",
    edit: "Edit",
    preview: "Preview",
    placeholder:
      "Example:\n2026-04-24 I tried five recursion tasks and passed two. factorial missed n == 0, and count_down kept recursing after n = 0.\nYou can also paste a course page link: https://...",
    example: "Load test case",
    file: "Attach file",
    noFile: "No file selected",
    analyze: "Generate advice",
    analyzing: "Analyzing",
    progressTitle: "AI Work Log",
    process: {
      parse: "Organize input materials",
      parseActive: "Reading the text box, links, and attachment into one learning trace.",
      index: "Index learning trace",
      indexActive: "Extracting learning events, concepts, evidence snippets, and retrieval chunks.",
      gaps: "Detect learning gaps",
      gapsActive: "Comparing recent performance, error patterns, and missing practice.",
      nudges: "Generate next action",
      nudgesActive: "Generating immediately actionable advice and an example exercise when useful.",
    },
    debug: "Debug mode",
    resultTitle: "Learning Advice & Practice Steps",
    emptyResult: "Submit learning materials to receive direct practice actions.",
    priority: "Priority",
    action: "Practice action",
    exercise: "Good starter exercise",
    materials: "Practice materials",
    steps: "Suggested steps",
    checklist: "Produce",
    previous: "Previous",
    next: "Next",
    advicePage: "Advice",
    concept: "Target concept",
    regenerate: "Regenerate",
    export: "Export result",
    debugTitle: "Debug Information",
    trace: "Trace Indexer output",
    gaps: "Gap Detector output",
    nudges: "Nudge Engine output",
    healthUnknown: "Backend unknown",
    ready: "Services ready",
    missing: "Config incomplete",
    language: "Language",
    attachmentHelp: "Supports .txt, .md, .csv, .pdf",
  },
};

export function App() {
  const [language, setLanguage] = useState<Language>("zh");
  const t = copy[language];
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [examples, setExamples] = useState<ExampleInfo[]>([]);
  const [exampleId, setExampleId] = useState("weak_recursion");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [debugMode, setDebugMode] = useState(false);
  const [inputMode, setInputMode] = useState<InputMode>("preview");
  const [processItems, setProcessItems] = useState<ProcessItem[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<"analyze" | "nudge" | "">("");

  const sourceInput = useMemo(
    () => ({ sourceType: "auto" as const, text, url: "", file, exampleId }),
    [text, file, exampleId]
  );

  useEffect(() => {
    getExamples().then(setExamples).catch((err: Error) => setError(err.message));
    getHealth().then(setHealth).catch((err: Error) => setError(err.message));
    loadExample("weak_recursion").catch((err: Error) => setError(err.message));
  }, []);

  async function loadExample(id: string) {
    setExampleId(id);
    setError("");
    const example = await getExampleBundle(id);
    setText(example.content);
    setFile(new File([example.file_content], example.file_name, { type: "text/markdown" }));
  }

  async function onAnalyze() {
    setBusy("analyze");
    setError("");
    setAnalysis(null);
    const baseItems = [
      { title: t.process.parse, detail: t.process.parseActive, status: "pending" as const },
      { title: t.process.index, detail: t.process.indexActive, status: "pending" as const },
      { title: t.process.gaps, detail: t.process.gapsActive, status: "pending" as const },
      { title: t.process.nudges, detail: t.process.nudgesActive, status: "pending" as const },
    ];
    setProcessItems(baseItems);
    const updateProcess = (index: number, status: ProcessStatus, detail: string) => {
      setProcessItems((items) =>
        items.map((item, itemIndex) => (itemIndex === index ? { ...item, status, detail } : item))
      );
    };
    try {
      updateProcess(0, "active", t.process.parseActive);
      const source = await parseSource(sourceInput);
      updateProcess(0, "done", doneParseDetail(language, source.raw_content.length, source.title));

      updateProcess(1, "active", t.process.indexActive);
      const traceIndex = await indexTrace(source);
      updateProcess(1, "done", doneIndexDetail(language, traceIndex.chunks_indexed, traceIndex.learning_events.length));

      updateProcess(2, "active", t.process.gapsActive);
      const gaps = await detectGaps(traceIndex.concept_index, traceIndex.learning_events);
      updateProcess(2, "done", doneGapDetail(language, gaps.length, gaps[0]?.concept));

      updateProcess(3, "active", t.process.nudgesActive);
      const nudges = await regenerateNudges(gaps);
      updateProcess(3, "done", doneNudgeDetail(language, nudges.length));

      setAnalysis({ trace_index: traceIndex, gaps, nudges });
      setProcessItems([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
      setProcessItems([]);
    } finally {
      setBusy("");
    }
  }

  async function onRegenerate() {
    if (!analysis) return;
    setBusy("nudge");
    setError("");
    setProcessItems([
      {
        title: t.process.nudges,
        detail: t.process.nudgesActive,
        status: "active",
      },
    ]);
    try {
      const nudges = await regenerateNudges(analysis.gaps);
      setAnalysis({ ...analysis, nudges });
      setProcessItems([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nudge generation failed.");
      setProcessItems([]);
    } finally {
      setBusy("");
    }
  }

  function exportResult() {
    if (!analysis) return;
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: "application/json" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = "action-tutor-analysis.json";
    link.click();
    URL.revokeObjectURL(href);
  }

  return (
    <main className="app-shell compact">
      <header className="topbar">
        <div>
          <p className="eyebrow">{t.eyebrow}</p>
          <h1>{t.title}</h1>
        </div>
        <div className="top-actions">
          <label className="language-select">
            <Languages size={16} />
            <span>{t.language}</span>
            <select value={language} onChange={(event) => setLanguage(event.target.value as Language)}>
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </label>
          <HealthBadge health={health} language={language} />
        </div>
      </header>

      {error && (
        <section className="notice error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </section>
      )}

      <section className="simple-layout">
        <article className="compose-panel">
          <div className="panel-heading">
            <ClipboardList size={18} />
            <h2>{t.inputTitle}</h2>
            <div className="input-mode-switch">
              <button className={inputMode === "edit" ? "active" : ""} onClick={() => setInputMode("edit")}>
                {t.edit}
              </button>
              <button className={inputMode === "preview" ? "active" : ""} onClick={() => setInputMode("preview")}>
                {t.preview}
              </button>
            </div>
          </div>
          <p className="helper-text">{t.inputHint}</p>

          {inputMode === "edit" ? (
            <textarea
              className="unified-input"
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder={t.placeholder}
              spellCheck={false}
            />
          ) : (
            <MarkdownPreview markdown={text || t.placeholder} />
          )}

          <div className="input-toolbar">
            <label className="field inline">
              <span>{t.example}</span>
              <select value={exampleId} onChange={(event) => loadExample(event.target.value)}>
                {examples.map((example) => (
                  <option key={example.example_id} value={example.example_id}>
                    {example.title}
                  </option>
                ))}
              </select>
            </label>

            <label className="file-picker">
              <Paperclip size={16} />
              <span>{file ? file.name : t.file}</span>
              <input
                type="file"
                accept=".txt,.md,.csv,.pdf"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>
            <span className="subtle">{file ? t.attachmentHelp : t.noFile}</span>
          </div>

          <div className="primary-actions">
            <button className="primary large" onClick={onAnalyze} disabled={Boolean(busy)}>
              {busy === "analyze" ? <Loader2 className="spin" size={17} /> : <Sparkles size={17} />}
              {busy === "analyze" ? t.analyzing : t.analyze}
            </button>
            <label className="debug-toggle">
              <input type="checkbox" checked={debugMode} onChange={(event) => setDebugMode(event.target.checked)} />
              <Settings2 size={16} />
              <span>{t.debug}</span>
            </label>
          </div>
        </article>

        <article className="advice-panel">
          <div className="panel-heading split">
            <div>
              <Play size={18} />
              <h2>{t.resultTitle}</h2>
            </div>
            <div className="result-actions">
              <button className="icon-button" onClick={onRegenerate} disabled={!analysis || Boolean(busy)} title={t.regenerate}>
                {busy === "nudge" ? <Loader2 className="spin" size={16} /> : <RefreshCcw size={16} />}
              </button>
              <button className="icon-button" onClick={exportResult} disabled={!analysis} title={t.export}>
                <Download size={16} />
              </button>
            </div>
          </div>

          {processItems.length > 0 && <ProcessLog items={processItems} title={t.progressTitle} />}
          {!analysis && busy !== "analyze" && <p className="empty">{t.emptyResult}</p>}
          {analysis && <AdviceList nudges={analysis.nudges} language={language} />}
        </article>
      </section>

      {debugMode && analysis && <DebugPanel analysis={analysis} language={language} />}
    </main>
  );
}

function ProcessLog({ items, title }: { items: ProcessItem[]; title: string }) {
  return (
    <section className="process-log">
      <div className="progress-title">
        <Sparkles size={16} />
        <strong>{title}</strong>
      </div>
      <ol>
        {items.map((item) => (
          <li key={item.title} className={item.status}>
            <span className="process-icon">
              {item.status === "done" && <CheckCircle2 size={15} />}
              {item.status === "active" && <Loader2 className="spin" size={15} />}
              {item.status === "pending" && <span className="pending-dot" />}
            </span>
            <span>
              <strong>{item.title}</strong>
              <small>{item.detail}</small>
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function MarkdownPreview({ markdown }: { markdown: string }) {
  const lines = markdown.split("\n");
  const nodes: ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (!line.trim()) {
      index += 1;
      continue;
    }

    if (line.startsWith("```")) {
      const code: string[] = [];
      index += 1;
      while (index < lines.length && !lines[index].startsWith("```")) {
        code.push(lines[index]);
        index += 1;
      }
      nodes.push(
        <pre key={`code-${index}`} className="markdown-code">
          <code>{code.join("\n")}</code>
        </pre>
      );
      index += 1;
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      const content = renderInlineMarkdown(heading[2]);
      if (level === 1) nodes.push(<h3 key={`h-${index}`}>{content}</h3>);
      if (level === 2) nodes.push(<h4 key={`h-${index}`}>{content}</h4>);
      if (level === 3) nodes.push(<h5 key={`h-${index}`}>{content}</h5>);
      index += 1;
      continue;
    }

    if (isTableStart(lines, index)) {
      const tableLines: string[] = [];
      while (index < lines.length && lines[index].includes("|")) {
        tableLines.push(lines[index]);
        index += 1;
      }
      nodes.push(renderMarkdownTable(tableLines, `table-${index}`));
      continue;
    }

    if (/^\s*[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^\s*[-*]\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*[-*]\s+/, ""));
        index += 1;
      }
      nodes.push(
        <ul key={`ul-${index}`}>
          {items.map((item, itemIndex) => (
            <li key={`${item}-${itemIndex}`}>{renderInlineMarkdown(item)}</li>
          ))}
        </ul>
      );
      continue;
    }

    const paragraph: string[] = [];
    while (
      index < lines.length &&
      lines[index].trim() &&
      !lines[index].startsWith("```") &&
      !lines[index].match(/^(#{1,3})\s+(.+)$/) &&
      !/^\s*[-*]\s+/.test(lines[index]) &&
      !isTableStart(lines, index)
    ) {
      paragraph.push(lines[index].replace(/\s{2}$/, ""));
      index += 1;
    }
    nodes.push(<p key={`p-${index}`}>{renderInlineMarkdown(paragraph.join(" "))}</p>);
  }

  return <div className="markdown-preview">{nodes}</div>;
}

function isTableStart(lines: string[], index: number): boolean {
  return Boolean(lines[index]?.includes("|") && lines[index + 1]?.match(/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/));
}

function renderMarkdownTable(lines: string[], key: string) {
  const rows = lines
    .filter((line, index) => index !== 1)
    .map((line) =>
      line
        .trim()
        .replace(/^\|/, "")
        .replace(/\|$/, "")
        .split("|")
        .map((cell) => cell.trim())
    );
  const [header, ...body] = rows;

  return (
    <div className="markdown-table-wrap" key={key}>
      <table>
        <thead>
          <tr>
            {header.map((cell, index) => (
              <th key={`${cell}-${index}`}>{renderInlineMarkdown(cell)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`}>
              {row.map((cell, cellIndex) => (
                <td key={`${cell}-${cellIndex}`}>{renderInlineMarkdown(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderInlineMarkdown(value: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(`[^`]+`|https?:\/\/[^\s)]+)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(value)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(value.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith("`")) {
      nodes.push(<code key={`${token}-${match.index}`}>{token.slice(1, -1)}</code>);
    } else {
      nodes.push(
        <a key={`${token}-${match.index}`} href={token} target="_blank" rel="noreferrer">
          {token}
        </a>
      );
    }
    lastIndex = match.index + token.length;
  }

  if (lastIndex < value.length) {
    nodes.push(value.slice(lastIndex));
  }

  return nodes;
}

function HealthBadge({ health, language }: { health: HealthResponse | null; language: Language }) {
  const t = copy[language];
  if (!health) {
    return <div className="health muted">{t.healthUnknown}</div>;
  }
  const ok = health.llm_configured && health.embedding_configured;
  return (
    <div className={ok ? "health ok" : "health warn"}>
      {ok ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
      <span>{ok ? t.ready : t.missing}</span>
    </div>
  );
}

function AdviceList({ nudges, language }: { nudges: Nudge[]; language: Language }) {
  const t = copy[language];
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    setActiveIndex(0);
  }, [nudges]);

  if (nudges.length === 0) {
    return null;
  }

  const activeNudge = nudges[Math.min(activeIndex, nudges.length - 1)];
  const canGoBack = activeIndex > 0;
  const canGoForward = activeIndex < nudges.length - 1;

  return (
    <div className="advice-list">
      <div className="advice-pager">
        <button
          className="icon-button"
          onClick={() => setActiveIndex((index) => Math.max(0, index - 1))}
          disabled={!canGoBack}
          title={t.previous}
        >
          <ChevronLeft size={17} />
        </button>
        <div className="pager-status">
          <strong>{t.advicePage} {activeIndex + 1}</strong>
          <span>/ {nudges.length}</span>
        </div>
        <button
          className="icon-button"
          onClick={() => setActiveIndex((index) => Math.min(nudges.length - 1, index + 1))}
          disabled={!canGoForward}
          title={t.next}
        >
          <ChevronRight size={17} />
        </button>
      </div>

      <section className="advice-card" key={`${activeNudge.concept}-${activeNudge.gap_type}-${activeIndex}`}>
        <div className="advice-index">{activeIndex + 1}</div>
        <div className="advice-body">
          <div className="advice-meta">
            <span>{t.concept}: {activeNudge.concept}</span>
            <span className={`priority ${activeNudge.priority}`}>{t.priority}: {activeNudge.priority}</span>
          </div>
          <p className="advice-text">{displayNudge(activeNudge, language)}</p>
          {displayPracticePrompt(activeNudge, language) && (
            <div className="mini-exercise">
              <strong>{t.exercise}{displayExerciseTitle(activeNudge, language) ? `：${displayExerciseTitle(activeNudge, language)}` : ""}</strong>
              <p>{displayPracticePrompt(activeNudge, language)}</p>
            </div>
          )}
          {displayPracticeMaterials(activeNudge, language).length > 0 && (
            <div className="practice-materials">
              <strong>{t.materials}</strong>
              <ul>
                {displayPracticeMaterials(activeNudge, language).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="practice-steps">
            <strong>{t.steps}</strong>
            <ol>
              {displayPracticeSteps(activeNudge, language).map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>
          {displaySubmissionChecklist(activeNudge, language).length > 0 && (
            <div className="practice-materials">
              <strong>{t.checklist}</strong>
              <ul>
                {displaySubmissionChecklist(activeNudge, language).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="practice-step">
            <FileText size={15} />
            <span>{t.action}: {displayActionType(activeNudge.action_type, language)}</span>
          </div>
          <p className="encouragement">{displayEncouragement(activeNudge, language)}</p>
        </div>
      </section>

      <div className="pager-dots" aria-label={`${t.advicePage} pages`}>
        {nudges.map((nudge, index) => (
          <button
            className={index === activeIndex ? "active" : ""}
            key={`${nudge.concept}-${nudge.gap_type}-${index}`}
            onClick={() => setActiveIndex(index)}
            title={`${t.advicePage} ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
}

function displayNudge(nudge: Nudge, language: Language): string {
  if (language === "en") {
    return nudge.nudge;
  }
  if (hasChinese(nudge.nudge)) {
    return nudge.nudge;
  }
  if (nudge.gap_type === "weak") {
    return `重新做一道关于「${nudge.concept}」的小题，并标出你上次最可能再次出错的位置。第一次检查失败后先停下来，写下一条修正规则。`;
  }
  if (nudge.gap_type === "avoided") {
    return `花 10 分钟启动一个你一直回避的「${nudge.concept}」练习。只写题目设置、第一步决策，以及一个你仍然答不上来的问题。`;
  }
  return `不要看笔记，先写出「${nudge.concept}」的核心规则，并用两个小例子测试它。圈出第一个让你不确定的地方。`;
}

function displayExerciseTitle(nudge: Nudge, language: Language): string {
  if (!nudge.exercise_title) {
    return "";
  }
  return nudge.exercise_title;
}

function displayPracticePrompt(nudge: Nudge, language: Language): string {
  if (!nudge.practice_prompt) {
    return "";
  }
  if (language === "en") {
    return nudge.practice_prompt;
  }
  if (hasChinese(nudge.practice_prompt)) {
    return nudge.practice_prompt;
  }
  return nudge.practice_prompt;
}

function displayPracticeMaterials(nudge: Nudge, language: Language): string[] {
  const materials = nudge.practice_materials ?? [];
  if (language === "en") {
    return materials;
  }
  if (materials.some(hasChinese)) {
    return materials;
  }
  return materials;
}

function displayPracticeSteps(nudge: Nudge, language: Language): string[] {
  const steps = nudge.practice_steps ?? [];
  if (language === "en") {
    return steps;
  }
  if (steps.some(hasChinese)) {
    return steps;
  }
  if (nudge.gap_type === "weak") {
    return ["先写最小输入或停止条件。", "再写第一步尝试，不要一次写完整答案。", "标出最可能再次出错的位置。", "写下一条下次避免该错误的规则。"];
  }
  if (nudge.gap_type === "avoided") {
    return ["用一句话重述题目。", "写出第一个变量、状态或规则。", "做一个不完整但真实的尝试。", "写出一个卡住你的具体问题。"];
  }
  return ["合上笔记，写出核心规则。", "用一个最小例子测试。", "再用一个边界例子测试。", "打开笔记前，圈出最不确定的一步。"];
}

function displaySubmissionChecklist(nudge: Nudge, language: Language): string[] {
  const checklist = nudge.submission_checklist ?? [];
  if (language === "en") {
    return checklist;
  }
  if (checklist.some(hasChinese)) {
    return checklist;
  }
  return checklist;
}

function displayEncouragement(nudge: Nudge, language: Language): string {
  if (language === "en") {
    return nudge.encouragement;
  }
  if (hasChinese(nudge.encouragement)) {
    return nudge.encouragement;
  }
  if (nudge.gap_type === "avoided") {
    return "先开始就很好，今天不需要一次做完。";
  }
  if (nudge.gap_type === "decaying") {
    return "这不是考试，只是在找记忆开始变模糊的位置。";
  }
  return "把题目做小一点，越具体越容易发现真正的薄弱点。";
}

function hasChinese(value: string): boolean {
  return /[\u4e00-\u9fff]/.test(value);
}

function displayActionType(actionType: string, language: Language): string {
  if (language === "en") {
    return actionType;
  }
  const labels: Record<string, string> = {
    "redo-and-mark": "重做并标记错误点",
    "start-and-state": "启动练习并写出第一步",
    "micro-exercise-and-mark": "微练习并标记错误点",
    "ten-minute-start": "十分钟启动练习",
    "retrieve-and-test": "主动回忆并测试",
  };
  return labels[actionType] ?? actionType;
}

function doneParseDetail(language: Language, length: number, title: string): string {
  if (language === "en") {
    return `Prepared ${length} characters from "${title}" for analysis.`;
  }
  return `已整理「${title}」中的 ${length} 个字符，接下来抽取学习事件。`;
}

function doneIndexDetail(language: Language, chunks: number, events: number): string {
  if (language === "en") {
    return `Indexed ${chunks} evidence chunks and extracted ${events} learning events.`;
  }
  return `已索引 ${chunks} 个证据片段，并抽取 ${events} 条学习事件。`;
}

function doneGapDetail(language: Language, gaps: number, topConcept?: string): string {
  if (language === "en") {
    return topConcept ? `Found ${gaps} learning gaps; top priority is ${topConcept}.` : "No major gap found.";
  }
  return topConcept ? `识别出 ${gaps} 个学习缺口，当前优先处理「${topConcept}」。` : "没有识别到明显学习缺口。";
}

function doneNudgeDetail(language: Language, nudges: number): string {
  if (language === "en") {
    return `Generated ${nudges} actionable recommendations.`;
  }
  return `已生成 ${nudges} 条可立即执行的学习建议。`;
}

function DebugPanel({ analysis, language }: { analysis: AnalysisResponse; language: Language }) {
  const t = copy[language];
  return (
    <section className="debug-panel">
      <div className="panel-heading">
        <Settings2 size={18} />
        <h2>{t.debugTitle}</h2>
      </div>
      <div className="debug-grid">
        <DebugBlock title={t.trace} value={analysis.trace_index} />
        <DebugBlock title={t.gaps} value={analysis.gaps} />
        <DebugBlock title={t.nudges} value={analysis.nudges} />
      </div>
    </section>
  );
}

function DebugBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <details className="debug-block">
      <summary>{title}</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}
