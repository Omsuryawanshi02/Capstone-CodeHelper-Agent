export type AgentName =
  | 'coordinator'
  | 'code_searcher'
  | 'code_explainer'
  | 'architecture_mapper'
  | 'onboarding_guide';

export type ActiveView = 'chat' | 'explorer' | 'architecture' | 'change_review';

export type ServiceStatus = 'connected' | 'disconnected' | 'error' | 'checking';

export interface ServiceHealthMap {
  backend: ServiceStatus;
  adk: ServiceStatus;
  pinecone: ServiceStatus;
  mcpFilesystem: ServiceStatus;
  mcpDrawio: ServiceStatus;
}

export interface SourceItem {
  filePath: string;
  startLine?: number | null;
  endLine?: number | null;
  snippet?: string | null;
  score?: number | null;
  type?: 'definition' | 'reference' | 'import' | 'docstring';
}

export interface StructuredAnswer {
  conclusion?: string;
  explanation?: string;
  limitations?: string;
  nextActions?: string[];
  confidence?: 'Confirmed' | 'Likely' | 'Unknown';
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  agentName?: AgentName | string;
  sources?: SourceItem[];
  activity?: string;
  isStreaming?: boolean;
  structuredAnswer?: StructuredAnswer;
  toolEvents?: Array<{ tool: string; durationMs: number; status: 'ok' | 'warn' | 'error'; summary: string }>;
}

export interface SessionItem {
  sessionId: string;
  title: string;
  createdAt: number;
  lastMessageAt?: number;
  messageCount: number;
}

export interface HealthState {
  status: 'ok' | 'degraded' | 'unhealthy' | 'checking';
  backendRunning: boolean;
  adkReachable: boolean;
  adkAppName: string;
  configValid: boolean;
  services?: ServiceHealthMap;
}

export interface NormalizedSSEEvent {
  type: 'status' | 'agent_activity' | 'token' | 'message' | 'source' | 'done' | 'error';
  session_id: string;
  text?: string;
  agent_name?: string;
  activity?: string;
  file_path?: string;
  start_line?: number;
  end_line?: number;
  snippet?: string;
  score?: number;
  error?: string;
}

// Codebase Explorer Types
export interface CodeFileNode {
  path: string;
  name: string;
  extension: string;
  sizeBytes: number;
  lineCount: number;
  functionsCount: number;
  classesCount: number;
  imports: string[];
  docstring?: string;
  content: string;
  astValid: boolean;
}

// Architecture Graph Types
export interface ModuleNode {
  id: string;
  name: string;
  path: string;
  lineCount: number;
  astSymbols: string[];
  incomingImports: string[];
  outgoingImports: string[];
  docstring: string;
  x?: number;
  y?: number;
}

export interface ModuleEdge {
  source: string;
  target: string;
  label?: string;
}

export interface ArchitectureData {
  modules: ModuleNode[];
  edges: ModuleEdge[];
  drawioUrl: string;
  mermaidCode: string;
  engine: 'deterministic-python-ast';
  llmUsed: false;
}

// Change Review Types
export interface DiffLine {
  type: 'add' | 'delete' | 'context';
  oldLineNumber?: number;
  newLineNumber?: number;
  text: string;
}

export interface ChangedFile {
  path: string;
  oldPath?: string;
  status: 'modified' | 'added' | 'deleted' | 'untracked';
  isStaged: boolean;
  additions: number;
  deletions: number;
  diffLines: DiffLine[];
  astDifferences: {
    addedFunctions: string[];
    modifiedFunctions: string[];
    removedFunctions: string[];
    addedClasses: string[];
    modifiedClasses: string[];
    syntaxError?: string;
  };
}

export interface ChangeReviewReport {
  branch: string;
  baseCommit: string;
  targetCommit: string;
  changedFiles: ChangedFile[];
  downstreamImpacts: {
    sourceFile: string;
    affectedCallers: string[];
  }[];
  riskLevel: 'Low' | 'Medium' | 'High';
  riskExplanation: string;
  confidence: 'Confirmed' | 'Likely' | 'Unknown';
  recommendedTests: string[];
}
