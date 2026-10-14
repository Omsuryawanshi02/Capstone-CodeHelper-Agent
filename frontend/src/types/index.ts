export type AgentName =
  | 'coordinator'
  | 'code_searcher'
  | 'code_explainer'
  | 'architecture_mapper'
  | 'onboarding_guide';

export interface SourceItem {
  filePath: string;
  startLine?: number | null;
  endLine?: number | null;
  snippet?: string | null;
  score?: number | null;
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
