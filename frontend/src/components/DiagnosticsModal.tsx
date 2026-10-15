import React, { useState } from 'react';
import {
  X,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Server,
  Terminal,
  Cpu,
  Database,
  FolderLock,
  WifiOff,
  Copy,
  Check,
  HelpCircle,
} from 'lucide-react';
import { HealthState } from '../types';

interface DiagnosticsModalProps {
  isOpen: boolean;
  onClose: () => void;
  health: HealthState;
  onRetryHealth: () => void;
}

type ErrorScenarioKey =
  | 'backend_offline'
  | 'adk_disconnected'
  | 'missing_project'
  | 'empty_search'
  | 'mcp_failure'
  | 'pinecone_failure'
  | 'stream_interrupted'
  | 'invalid_request';

interface ErrorScenario {
  id: ErrorScenarioKey;
  title: string;
  category: string;
  icon: React.ReactNode;
  severity: 'error' | 'warning';
  summary: string;
  technicalDetails: string;
  recoverySteps: string[];
  suggestedCommand?: string;
}

export const DiagnosticsModal: React.FC<DiagnosticsModalProps> = ({
  isOpen,
  onClose,
  health,
  onRetryHealth,
}) => {
  const [selectedScenarioKey, setSelectedScenarioKey] =
    useState<ErrorScenarioKey>('backend_offline');
  const [copiedCmd, setCopiedCmd] = useState(false);

  if (!isOpen) return null;

  const scenarios: ErrorScenario[] = [
    {
      id: 'backend_offline',
      title: 'Backend Unavailable (:8001)',
      category: 'Network / Fast API',
      icon: <Server className="h-4 w-4 text-red-err" />,
      severity: 'error',
      summary:
        'The React frontend cannot establish an HTTP or SSE connection to the FastAPI integration backend on port 8001.',
      technicalDetails:
        'Failed to fetch http://127.0.0.1:8001/api/health. Connection refused (ERR_CONNECTION_REFUSED). Requests cannot be normalized or tracked.',
      recoverySteps: [
        'Ensure the Python virtual environment is activated.',
        'Run the backend server using uvicorn on port 8001.',
        'Verify firewall rules allow localhost TCP loopback on port 8001.',
        'Click "Retry Health Check" below once started.',
      ],
      suggestedCommand: 'python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload',
    },
    {
      id: 'adk_disconnected',
      title: 'Google ADK Runtime Disconnected (:8000)',
      category: 'Agent Runtime',
      icon: <Cpu className="h-4 w-4 text-amber-warn" />,
      severity: 'warning',
      summary:
        'The FastAPI backend is running, but the Google ADK multi-agent runtime on port 8000 is unreachable or in standby mode.',
      technicalDetails:
        'ADK API Client timeout on http://127.0.0.1:8000/run_sse (App: "code_helper"). Coordinator root_agent cannot receive live events.',
      recoverySteps: [
        'Verify Google ADK CLI is installed and in path (adk --version).',
        'Start the code_helper multi-agent application via ADK on port 8000.',
        'Verify GEMINI_API_KEY and NVIDIA_API_KEY environment variables are exported in .env.',
        'Inspect code_helper/agent.py root_agent definition.',
      ],
      suggestedCommand: 'adk run code_helper --port 8000',
    },
    {
      id: 'missing_project',
      title: 'Missing Project Selection',
      category: 'Workspace State',
      icon: <FolderLock className="h-4 w-4 text-amber-warn" />,
      severity: 'warning',
      summary:
        'No valid target codebase directory is selected or indexed for retrieval.',
      technicalDetails:
        'Target path "target_project" does not exist or lacks Python source files. AST indexer skipped file discovery.',
      recoverySteps: [
        'Verify target_project exists at workspace root (d:/deboistech/demo/target_project).',
        'Ensure directory contains at least one valid .py file.',
        'Run code_helper indexer to populate metadata.',
      ],
      suggestedCommand: 'python -m code_helper.index_codebase',
    },
    {
      id: 'empty_search',
      title: 'Empty Search Results',
      category: 'Pinecone Vector Retrieval',
      icon: <HelpCircle className="h-4 w-4 text-cyan-source" />,
      severity: 'warning',
      summary:
        'The query was processed successfully, but cosine similarity did not yield chunks above the relevance threshold (0.75).',
      technicalDetails:
        'Pinecone query completed in 42ms with 0 matches above score threshold. Index: code-helper-index (1024-dim, cosine).',
      recoverySteps: [
        'Reformulate your question with specific Python keywords (e.g. "retrieve_relevant_chunks", "config", "upsert").',
        'Ask the assistant to explore the file tree directly in Codebase Explorer.',
        'Trigger deterministic architecture inspection instead of vector search.',
      ],
      suggestedCommand: 'Ask: "What functions are defined in target_project/config.py?"',
    },
    {
      id: 'mcp_failure',
      title: 'Filesystem MCP Failure',
      category: 'Model Context Protocol',
      icon: <FolderLock className="h-4 w-4 text-red-err" />,
      severity: 'error',
      summary:
        'Filesystem MCP server rejected file access due to security sandbox boundaries or missing read permissions.',
      technicalDetails:
        '@modelcontextprotocol/server-filesystem error: Path traversal prohibited outside authorized workspace root.',
      recoverySteps: [
        'Verify relative file paths reside inside target_project/.',
        'Ensure node and @modelcontextprotocol/server-filesystem are executable.',
        'Check filesystem read permissions for current process user.',
      ],
      suggestedCommand: 'npx -y @modelcontextprotocol/server-filesystem target_project',
    },
    {
      id: 'pinecone_failure',
      title: 'Pinecone Retrieval Failure (Offline Fallback)',
      category: 'Vector Database',
      icon: <Database className="h-4 w-4 text-amber-warn" />,
      severity: 'warning',
      summary:
        'Pinecone serverless index connection timed out or PINECONE_API_KEY is unconfigured.',
      technicalDetails:
        'pinecone.exceptions.PineconeApiException: 401 Unauthorized. Gracefully falling back to AST static analysis and Filesystem MCP.',
      recoverySteps: [
        'Add valid PINECONE_API_KEY and PINECONE_INDEX_NAME to .env.',
        'Verify Pinecone region: us-east-1 (aws serverless).',
        'The assistant will automatically use deterministic AST and Filesystem MCP in offline mode.',
      ],
      suggestedCommand: 'python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(bool(os.getenv(\'PINECONE_API_KEY\')))"',
    },
    {
      id: 'stream_interrupted',
      title: 'Stream Interrupted / Aborted',
      category: 'SSE Stream Lifecycle',
      icon: <WifiOff className="h-4 w-4 text-red-err" />,
      severity: 'error',
      summary:
        'Server-Sent Events connection was terminated before the "done" event was received.',
      technicalDetails:
        'EventSource connection error: SSE stream aborted by client AbortController or network socket drop.',
      recoverySteps: [
        'Click the "Retry Last Turn" button in the message composer.',
        'Verify backend is not terminating worker threads prematurely.',
        'Inspect FastAPI logs at backend/app/routes/chat.py for unhandled exceptions.',
      ],
    },
    {
      id: 'invalid_request',
      title: 'Invalid Request / Syntax Error',
      category: 'Input Validation',
      icon: <XCircle className="h-4 w-4 text-red-err" />,
      severity: 'error',
      summary:
        'The query contained unparseable syntax or requested unauthorized operations.',
      technicalDetails:
        'HTTP 422 Unprocessable Entity. Message payload validation failed in backend schema.',
      recoverySteps: [
        'Ensure input is non-empty string under 4000 characters.',
        'Remove unescaped control characters or null bytes.',
        'Use the message composer input with valid UTF-8 text.',
      ],
    },
  ];

  const currentScenario =
    scenarios.find((s) => s.id === selectedScenarioKey) || scenarios[0];

  const handleCopyCmd = async (cmd: string) => {
    try {
      await navigator.clipboard.writeText(cmd);
      setCopiedCmd(true);
      setTimeout(() => setCopiedCmd(false), 2000);
    } catch (err) {
      console.error('Failed to copy command:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div className="flex h-[88vh] w-full max-w-4xl flex-col rounded-2xl border border-obsidian-border bg-obsidian-bg shadow-panel overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-obsidian-border bg-obsidian-subtle px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-obsidian-elevated border border-obsidian-border text-amber-warn">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-cockpit-text">
                Service Diagnostics & Error States (Screen F)
              </h2>
              <p className="text-[11px] text-cockpit-muted">
                Inspect system connectivity and verify failure recovery procedures
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onRetryHealth}
              className="flex items-center gap-1.5 rounded-lg border border-obsidian-border bg-obsidian-elevated px-3 py-1.5 text-xs text-cockpit-muted hover:text-cockpit-text hover:border-lime-accent/50 transition-colors cursor-pointer"
            >
              <RefreshCw className="h-3.5 w-3.5 text-lime-accent" />
              <span>Retry Health Check</span>
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-cockpit-muted hover:bg-obsidian-elevated hover:text-cockpit-text transition-colors cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Live Services Status Strip */}
        <div className="border-b border-obsidian-border bg-obsidian-subtle/50 px-6 py-2.5 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span
                className={`h-2 w-2 rounded-full ${
                  health.backendRunning ? 'bg-lime-accent' : 'bg-red-err'
                }`}
              />
              <span className="text-cockpit-muted">Backend (:8001):</span>
              <span className={health.backendRunning ? 'text-lime-accent' : 'text-red-err'}>
                {health.backendRunning ? 'Online' : 'Offline'}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <span
                className={`h-2 w-2 rounded-full ${
                  health.adkReachable ? 'bg-lime-accent' : 'bg-amber-warn'
                }`}
              />
              <span className="text-cockpit-muted">ADK Runtime (:8000):</span>
              <span className={health.adkReachable ? 'text-lime-accent' : 'text-amber-warn'}>
                {health.adkReachable ? 'Connected' : 'Standby'}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-lime-accent" />
              <span className="text-cockpit-muted">Deterministic AST:</span>
              <span className="text-lime-accent">100% Ready</span>
            </div>
          </div>

          <div className="text-[11px] text-cockpit-faint">
            App: <span className="text-cockpit-text">{health.adkAppName}</span>
          </div>
        </div>

        {/* Modal Main Content: Left Scenarios List, Right Details */}
        <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
          {/* Left: Scenarios Selector (~300px) */}
          <div className="w-full md:w-80 border-b md:border-b-0 md:border-r border-obsidian-border bg-obsidian-subtle/40 overflow-y-auto p-2 space-y-1">
            <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-cockpit-muted">
              Select Error Scenario to Inspect
            </div>
            {scenarios.map((s) => {
              const isSelected = s.id === selectedScenarioKey;
              return (
                <button
                  key={s.id}
                  onClick={() => setSelectedScenarioKey(s.id)}
                  className={`flex w-full items-start gap-2.5 rounded-xl p-2.5 text-left text-xs transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-obsidian-elevated border border-obsidian-border text-cockpit-text'
                      : 'hover:bg-obsidian-subtle text-cockpit-muted'
                  }`}
                >
                  <div className="mt-0.5 shrink-0">{s.icon}</div>
                  <div className="truncate flex-1">
                    <span className="font-semibold block truncate text-cockpit-text">
                      {s.title}
                    </span>
                    <span className="text-[10px] text-cockpit-faint block truncate">
                      {s.category}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right: Detailed Error Breakdown & Actionable Recovery */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-obsidian-bg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {currentScenario.icon}
                <h3 className="text-base font-semibold text-cockpit-text">
                  {currentScenario.title}
                </h3>
              </div>
              <span
                className={`rounded px-2 py-0.5 font-mono text-[10px] uppercase border ${
                  currentScenario.severity === 'error'
                    ? 'border-red-err/40 bg-red-err/10 text-red-err'
                    : 'border-amber-warn/40 bg-amber-warn/10 text-amber-warn'
                }`}
              >
                {currentScenario.severity}
              </span>
            </div>

            {/* Error Summary */}
            <div className="rounded-xl border border-obsidian-border bg-obsidian-subtle p-4 space-y-2">
              <span className="font-semibold text-cockpit-muted uppercase tracking-wider text-[11px] block">
                Impact Summary
              </span>
              <p className="text-xs text-cockpit-text leading-relaxed font-medium">
                {currentScenario.summary}
              </p>
            </div>

            {/* Technical Diagnostic Message */}
            <div className="rounded-xl border border-obsidian-border bg-obsidian-bg p-4 space-y-2 font-mono text-xs">
              <span className="font-semibold text-cockpit-faint uppercase tracking-wider text-[10px] block font-sans">
                Technical Exception Output
              </span>
              <div className="text-red-err text-[11px] leading-relaxed whitespace-pre-wrap">
                {currentScenario.technicalDetails}
              </div>
            </div>

            {/* Actionable Recovery Instructions */}
            <div className="space-y-2">
              <span className="font-semibold text-cockpit-muted uppercase tracking-wider text-[11px] block">
                What You Can Do Next (Recovery Guide)
              </span>
              <ol className="space-y-2 text-xs text-cockpit-text list-decimal pl-4 leading-relaxed">
                {currentScenario.recoverySteps.map((step, idx) => (
                  <li key={idx} className="pl-1">
                    {step}
                  </li>
                ))}
              </ol>
            </div>

            {/* Suggested Command */}
            {currentScenario.suggestedCommand && (
              <div className="space-y-2 pt-2">
                <span className="font-semibold text-cockpit-muted uppercase tracking-wider text-[11px] block">
                  Suggested Terminal Command
                </span>
                <div className="flex items-center justify-between rounded-xl border border-obsidian-border bg-obsidian-subtle px-3.5 py-2.5 font-mono text-xs text-lime-accent">
                  <div className="flex items-center gap-2 truncate">
                    <Terminal className="h-4 w-4 text-cockpit-muted shrink-0" />
                    <span className="truncate">{currentScenario.suggestedCommand}</span>
                  </div>
                  <button
                    onClick={() => handleCopyCmd(currentScenario.suggestedCommand!)}
                    className="p-1 text-cockpit-muted hover:text-cockpit-text rounded transition-colors cursor-pointer"
                    title="Copy command"
                  >
                    {copiedCmd ? (
                      <Check className="h-3.5 w-3.5 text-lime-accent" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
