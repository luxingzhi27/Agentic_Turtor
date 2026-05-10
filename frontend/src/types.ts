export type SourceType = "text" | "file" | "url" | "example" | "auto";
export type GapType = "weak" | "avoided" | "decaying";

export interface ExampleInfo {
  example_id: string;
  title: string;
  description: string;
}

export interface ExampleBundle {
  example_id: string;
  title: string;
  content: string;
  file_name: string;
  file_content: string;
}

export interface SourceMetadata {
  url: string | null;
  filename: string | null;
  captured_at: string;
  content_type: string | null;
  parser: string;
}

export interface NormalizedSource {
  source_id: string;
  source_type: SourceType;
  title: string;
  raw_content: string;
  metadata: SourceMetadata;
}

export interface Evidence {
  source_id: string;
  quote: string;
  location: string | null;
}

export interface Performance {
  score: number | null;
  confidence: number | null;
  attempts: number | null;
}

export interface LearningEvent {
  event_id: string;
  timestamp: string | null;
  type: string;
  concepts: string[];
  summary: string;
  performance: Performance;
  errors: string[];
  evidence: Evidence[];
  extraction_confidence: number;
}

export interface ConceptStats {
  events: number;
  last_seen: string | null;
  average_score: number | null;
  average_confidence: number | null;
  common_errors: string[];
  evidence_sources: string[];
  summaries: string[];
}

export interface TraceIndexResponse {
  source: NormalizedSource;
  chunks_indexed: number;
  learning_events: LearningEvent[];
  concept_index: Record<string, ConceptStats>;
}

export interface Gap {
  concept: string;
  gap_type: GapType;
  severity: number;
  evidence: string[];
  calculation_notes: string[];
}

export interface Nudge {
  concept: string;
  gap_type: GapType;
  nudge: string;
  action_type: string;
  exercise_title?: string | null;
  practice_prompt?: string | null;
  practice_materials: string[];
  practice_steps: string[];
  submission_checklist: string[];
  encouragement: string;
  priority: "low" | "medium" | "high";
  passed_guardrail: boolean;
}

export interface AnalysisResponse {
  trace_index: TraceIndexResponse;
  gaps: Gap[];
  nudges: Nudge[];
}

export interface HealthResponse {
  status: "ok";
  llm_configured: boolean;
  embedding_configured: boolean;
  chroma_dir: string;
  python_runtime: string;
}
