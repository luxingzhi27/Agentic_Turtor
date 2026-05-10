import type {
  AnalysisResponse,
  ConceptStats,
  ExampleBundle,
  ExampleInfo,
  Gap,
  HealthResponse,
  LearningEvent,
  NormalizedSource,
  Nudge,
  TraceIndexResponse
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export interface SourceInput {
  sourceType: "text" | "file" | "url" | "example" | "auto";
  text: string;
  url: string;
  exampleId: string;
  file: File | null;
}

function sourceForm(input: SourceInput): FormData {
  const form = new FormData();
  form.append("source_type", input.sourceType);
  if (input.text) form.append("text", input.text);
  if (input.url) form.append("url", input.url);
  if (input.exampleId) form.append("example_id", input.exampleId);
  if (input.file) form.append("file", input.file);
  return form;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    let message = text || `Request failed with ${response.status}`;
    try {
      const parsed = JSON.parse(text);
      const detail = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail);
      message = detail || message;
    } catch {
      message = text || message;
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return parseResponse<HealthResponse>(await fetch(`${API_BASE}/api/health`));
}

export async function getExamples(): Promise<ExampleInfo[]> {
  return parseResponse<ExampleInfo[]>(await fetch(`${API_BASE}/api/examples`));
}

export async function getExampleContent(exampleId: string): Promise<{ title: string; content: string }> {
  return parseResponse<{ title: string; content: string }>(await fetch(`${API_BASE}/api/examples/${exampleId}`));
}

export async function getExampleBundle(exampleId: string): Promise<ExampleBundle> {
  return parseResponse<ExampleBundle>(await fetch(`${API_BASE}/api/examples/${exampleId}/bundle`));
}

export async function parseSource(input: SourceInput): Promise<NormalizedSource> {
  return parseResponse<NormalizedSource>(
    await fetch(`${API_BASE}/api/sources/parse`, {
      method: "POST",
      body: sourceForm(input)
    })
  );
}

export async function analyze(input: SourceInput): Promise<AnalysisResponse> {
  return parseResponse<AnalysisResponse>(
    await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      body: sourceForm(input)
    })
  );
}

export async function indexTrace(source: NormalizedSource): Promise<TraceIndexResponse> {
  return parseResponse<TraceIndexResponse>(
    await fetch(`${API_BASE}/api/traces/index`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(source)
    })
  );
}

export async function detectGaps(
  conceptIndex: Record<string, ConceptStats>,
  learningEvents: LearningEvent[]
): Promise<Gap[]> {
  const response = await parseResponse<{ gaps: Gap[] }>(
    await fetch(`${API_BASE}/api/gaps/detect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ concept_index: conceptIndex, learning_events: learningEvents })
    })
  );
  return response.gaps;
}

export async function regenerateNudges(gaps: AnalysisResponse["gaps"]): Promise<Nudge[]> {
  const response = await parseResponse<{ nudges: Nudge[] }>(
    await fetch(`${API_BASE}/api/nudges/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gaps })
    })
  );
  return response.nudges;
}
