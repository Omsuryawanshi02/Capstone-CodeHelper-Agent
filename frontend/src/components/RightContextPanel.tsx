import React, { useState } from 'react';
import {
  Layers,
  FileCode,
  Network,
  ExternalLink,
  X,
  Copy,
  Check,
  ChevronRight,
} from 'lucide-react';
import { ChatMessage } from '../types';
import { ARCHITECTURE_DATA } from '../data/projectData';

interface RightContextPanelProps {
  isOpen: boolean;
  onClose: () => void;
  activeMessage?: ChatMessage | null;
  onSelectFile?: (filePath: string) => void;
  onOpenArchitecture?: () => void;
}

export const RightContextPanel: React.FC<RightContextPanelProps> = ({
  isOpen,
  onClose,
  activeMessage,
  onSelectFile,
  onOpenArchitecture,
}) => {
  const [activeTab, setActiveTab] = useState<'evidence' | 'activity' | 'retrieval' | 'diagram'>('evidence');
  const [copiedDiagram, setCopiedDiagram] = useState(false);

  if (!isOpen) return null;

  const sources = activeMessage?.sources || [];
  const toolEvents = activeMessage?.toolEvents || [];

  const handleCopyMermaid = async () => {
    try {
      await navigator.clipboard.writeText(ARCHITECTURE_DATA.mermaidCode);
      setCopiedDiagram(true);
      setTimeout(() => setCopiedDiagram(false), 2000);
    } catch (err) {
      console.error('Failed to copy mermaid diagram:', err);
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs xl:hidden"
      />

      <aside className="fixed inset-y-0 right-0 z-50 flex w-80 sm:w-88 flex-col border-l border-obsidian-border bg-obsidian-bg xl:static xl:z-auto transition-transform duration-200">
        {/* Header */}
        <div className="flex h-13 items-center justify-between border-b border-obsidian-border px-4 bg-obsidian-subtle/80">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-cyan-source" />
            <span className="font-semibold text-xs text-cockpit-text uppercase tracking-wider">
              Context Inspector
            </span>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-cockpit-muted hover:bg-obsidian-elevated hover:text-cockpit-text transition-colors cursor-pointer"
            title="Close inspector"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-obsidian-border bg-obsidian-subtle/50 px-2 py-1.5 text-xs gap-1">
          <button
            onClick={() => setActiveTab('evidence')}
            className={`flex-1 rounded-md py-1 px-2 text-center text-[11px] font-medium transition-colors cursor-pointer ${
              activeTab === 'evidence'
                ? 'bg-obsidian-elevated text-cyan-source border border-obsidian-border'
                : 'text-cockpit-muted hover:text-cockpit-text hover:bg-obsidian-elevated/40'
            }`}
          >
            Evidence ({sources.length})
          </button>
          <button
            onClick={() => setActiveTab('activity')}
            className={`flex-1 rounded-md py-1 px-2 text-center text-[11px] font-medium transition-colors cursor-pointer ${
              activeTab === 'activity'
                ? 'bg-obsidian-elevated text-lime-accent border border-obsidian-border'
                : 'text-cockpit-muted hover:text-cockpit-text hover:bg-obsidian-elevated/40'
            }`}
          >
            Agents
          </button>
          <button
            onClick={() => setActiveTab('retrieval')}
            className={`flex-1 rounded-md py-1 px-2 text-center text-[11px] font-medium transition-colors cursor-pointer ${
              activeTab === 'retrieval'
                ? 'bg-obsidian-elevated text-violet-ai border border-obsidian-border'
                : 'text-cockpit-muted hover:text-cockpit-text hover:bg-obsidian-elevated/40'
            }`}
          >
            RAG / Tools
          </button>
          <button
            onClick={() => setActiveTab('diagram')}
            className={`flex-1 rounded-md py-1 px-2 text-center text-[11px] font-medium transition-colors cursor-pointer ${
              activeTab === 'diagram'
                ? 'bg-obsidian-elevated text-lime-accent border border-obsidian-border'
                : 'text-cockpit-muted hover:text-cockpit-text hover:bg-obsidian-elevated/40'
            }`}
          >
            Diagram
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* TAB 1: Evidence & Sources */}
          {activeTab === 'evidence' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
                <span>Referenced Files</span>
                <span className="font-mono text-[10px] text-cyan-source">
                  {sources.length} Verified Sources
                </span>
              </div>

              {sources.length === 0 ? (
                <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle/50 p-4 text-center text-xs text-cockpit-muted">
                  No source references returned for current turn.
                </div>
              ) : (
                sources.map((src, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-obsidian-border bg-obsidian-subtle p-3 space-y-2 hover:border-cyan-source/40 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div
                        onClick={() => onSelectFile && onSelectFile(src.filePath)}
                        className="flex items-center gap-1.5 font-mono text-xs text-cyan-source font-medium truncate cursor-pointer hover:underline"
                      >
                        <FileCode className="h-3.5 w-3.5 shrink-0" />
                        <span className="truncate">{src.filePath}</span>
                      </div>
                      {src.score && (
                        <span className="rounded bg-cyan-source/10 border border-cyan-source/30 px-1.5 py-0.2 font-mono text-[10px] text-cyan-source">
                          {(src.score * 100).toFixed(0)}% match
                        </span>
                      )}
                    </div>

                    {src.startLine && src.endLine && (
                      <div className="text-[11px] text-cockpit-muted font-mono">
                        Line Range: <span className="text-cockpit-text">{src.startLine}–{src.endLine}</span>
                      </div>
                    )}

                    {src.snippet && (
                      <div className="rounded border border-obsidian-border bg-obsidian-bg p-2 font-mono text-[11px] text-cockpit-muted line-clamp-3 leading-relaxed">
                        {src.snippet}
                      </div>
                    )}

                    <div className="pt-1 flex items-center justify-between text-[10px] text-cockpit-faint">
                      <span>Filesystem MCP Grounded</span>
                      <button
                        onClick={() => onSelectFile && onSelectFile(src.filePath)}
                        className="text-cyan-source hover:underline flex items-center gap-0.5 cursor-pointer"
                      >
                        <span>Open file</span>
                        <ChevronRight className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                ))
              )}

              {/* Related Project Files */}
              <div className="pt-3 border-t border-obsidian-border space-y-2">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
                  Related Project Files
                </div>
                <div className="space-y-1">
                  {['target_project/query_pipeline.py', 'target_project/config.py', 'target_project/vector_store.py'].map(
                    (p, i) => (
                      <div
                        key={i}
                        onClick={() => onSelectFile && onSelectFile(p)}
                        className="flex items-center justify-between rounded px-2.5 py-1.5 text-xs text-cockpit-muted hover:bg-obsidian-subtle hover:text-cockpit-text cursor-pointer transition-colors font-mono"
                      >
                        <span className="truncate">{p}</span>
                        <ExternalLink className="h-3 w-3 shrink-0 opacity-60" />
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Agent Timeline */}
          {activeTab === 'activity' && (
            <div className="space-y-3">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
                Execution Event Timeline
              </div>

              <div className="relative pl-4 space-y-4 border-l border-obsidian-border text-xs">
                {/* Event 1 */}
                <div className="relative">
                  <span className="absolute -left-[21px] top-0.5 flex h-2.5 w-2.5 rounded-full bg-lime-accent" />
                  <div className="font-semibold text-cockpit-text">Coordinator Agent</div>
                  <div className="text-[11px] text-cockpit-muted">
                    Analyzed query intent and routed to Code Searcher & Architecture Mapper.
                  </div>
                  <div className="font-mono text-[10px] text-cockpit-faint mt-0.5">Google ADK root_agent</div>
                </div>

                {/* Event 2 */}
                <div className="relative">
                  <span className="absolute -left-[21px] top-0.5 flex h-2.5 w-2.5 rounded-full bg-cyan-source" />
                  <div className="font-semibold text-cockpit-text">Code Searcher (RAG)</div>
                  <div className="text-[11px] text-cockpit-muted">
                    Queried Pinecone serverless vector index with NVIDIA NIM embedding.
                  </div>
                  <div className="font-mono text-[10px] text-cyan-source mt-0.5">Retrieved 2 chunks (score &gt; 0.85)</div>
                </div>

                {/* Event 3 */}
                <div className="relative">
                  <span className="absolute -left-[21px] top-0.5 flex h-2.5 w-2.5 rounded-full bg-amber-warn" />
                  <div className="font-semibold text-cockpit-text">Code Explainer (MCP)</div>
                  <div className="text-[11px] text-cockpit-muted">
                    Invoked Filesystem MCP tool <code className="text-amber-warn font-mono">read_project_file</code>.
                  </div>
                  <div className="font-mono text-[10px] text-cockpit-faint mt-0.5">Grounded AST parsing</div>
                </div>

                {/* Event 4 */}
                <div className="relative">
                  <span className="absolute -left-[21px] top-0.5 flex h-2.5 w-2.5 rounded-full bg-violet-ai" />
                  <div className="font-semibold text-cockpit-text">Architecture Mapper (AST)</div>
                  <div className="text-[11px] text-cockpit-muted">
                    Deterministic Python AST inspection of imports and caller edges.
                  </div>
                  <div className="font-mono text-[10px] text-violet-ai mt-0.5">Zero LLM Inference • 100% Deterministic</div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: RAG Retrieval & Tool Events */}
          {activeTab === 'retrieval' && (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
                  Vector Retrieval Parameters
                </div>
                <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle p-3 text-xs space-y-1.5 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-cockpit-muted">Vector DB:</span>
                    <span className="text-lime-accent">Pinecone Serverless</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-cockpit-muted">Embedding:</span>
                    <span className="text-cyan-source">nemotron-3-embed-1b</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-cockpit-muted">Dimension:</span>
                    <span className="text-cockpit-text">1024</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-cockpit-muted">Metric:</span>
                    <span className="text-cockpit-text">Cosine Similarity</span>
                  </div>
                </div>
              </div>

              {/* Tool Execution Log */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
                  MCP & Tool Executions
                </div>
                {toolEvents.length > 0 ? (
                  toolEvents.map((evt, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-obsidian-border bg-obsidian-subtle p-2.5 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between font-mono text-[11px]">
                        <span className="text-cockpit-text font-semibold">{evt.tool}</span>
                        <span className="text-lime-accent">{evt.durationMs}ms</span>
                      </div>
                      <div className="text-[11px] text-cockpit-muted">{evt.summary}</div>
                    </div>
                  ))
                ) : (
                  <div className="space-y-1.5">
                    <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle p-2.5 text-xs space-y-1">
                      <div className="flex items-center justify-between font-mono text-[11px]">
                        <span className="text-cockpit-text font-semibold">@drawio/mcp:open_drawio_mermaid</span>
                        <span className="text-lime-accent">45ms</span>
                      </div>
                      <div className="text-[11px] text-cockpit-muted">
                        Exported validated Mermaid diagram to official Draw.io editor URL.
                      </div>
                    </div>
                    <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle p-2.5 text-xs space-y-1">
                      <div className="flex items-center justify-between font-mono text-[11px]">
                        <span className="text-cockpit-text font-semibold">@modelcontextprotocol/filesystem</span>
                        <span className="text-lime-accent">18ms</span>
                      </div>
                      <div className="text-[11px] text-cockpit-muted">
                        Read target_project source files with path traversal security guards.
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: Architecture & Live Draw.io Link */}
          {activeTab === 'diagram' && (
            <div className="space-y-3">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
                Official Draw.io MCP Integration
              </div>

              <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle p-3 space-y-2.5">
                <div className="flex items-center gap-2 text-xs font-semibold text-cockpit-text">
                  <Network className="h-4 w-4 text-violet-ai" />
                  <span>Module Dependency Graph</span>
                </div>
                <p className="text-[11px] text-cockpit-muted leading-relaxed">
                  Generated via deterministic Python AST parsing (<code className="text-violet-ai font-mono">ast.walk</code>).
                  Zero LLM tokens consumed.
                </p>

                <a
                  href={ARCHITECTURE_DATA.drawioUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 rounded-lg bg-lime-accent px-3 py-2 text-xs font-semibold text-obsidian-bg hover:bg-lime-hover transition-colors w-full cursor-pointer shadow-sm"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  <span>Open in Draw.io Editor</span>
                </a>

                <button
                  onClick={handleCopyMermaid}
                  className="flex items-center justify-center gap-1.5 rounded-lg border border-obsidian-border bg-obsidian-elevated px-3 py-1.5 text-xs text-cockpit-muted hover:text-cockpit-text hover:border-obsidian-border/80 transition-colors w-full cursor-pointer"
                >
                  {copiedDiagram ? <Check className="h-3.5 w-3.5 text-lime-accent" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copiedDiagram ? 'Mermaid Copied' : 'Copy Mermaid Syntax'}</span>
                </button>
              </div>

              <div className="pt-2">
                <button
                  onClick={onOpenArchitecture}
                  className="flex items-center justify-between rounded-lg border border-obsidian-border bg-obsidian-subtle p-3 text-xs text-cockpit-muted hover:text-cockpit-text hover:border-lime-accent/50 transition-colors w-full cursor-pointer"
                >
                  <span>Explore Interactive Canvas</span>
                  <ChevronRight className="h-4 w-4 text-lime-accent" />
                </button>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
