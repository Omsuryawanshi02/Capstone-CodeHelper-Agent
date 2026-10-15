import React from 'react';
import { Search, FileCode, Network, GitBranch, Terminal, ShieldCheck } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt?: (prompt: string) => void;
  onNavigateTab?: (tab: 'chat' | 'explorer' | 'architecture' | 'change_review') => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt, onNavigateTab }) => {
  const starterActions = [
    {
      id: 'find_code',
      title: 'Find Code',
      icon: <Search className="h-4 w-4 text-cyan-source" />,
      tag: 'Pinecone RAG + NVIDIA NIM',
      prompt: 'Where is the query pipeline embedding logic in target_project, and how does it interface with Pinecone?',
      desc: 'Locate functions, constants, and semantic implementations across the indexed codebase.',
      viewTab: 'chat' as const,
    },
    {
      id: 'explain_file',
      title: 'Explain a File',
      icon: <FileCode className="h-4 w-4 text-amber-warn" />,
      tag: 'Filesystem MCP',
      prompt: 'Explain target_project/config.py, its environment variables, and validation rules.',
      desc: 'Analyze full file context, imports, security, and class/function responsibilities.',
      viewTab: 'explorer' as const,
    },
    {
      id: 'map_arch',
      title: 'Map Architecture',
      icon: <Network className="h-4 w-4 text-violet-ai" />,
      tag: 'Deterministic AST • Zero LLM',
      prompt: 'Inspect imports in target_project and generate a module dependency graph with draw.io diagram.',
      desc: 'Deterministic Python AST import graph with zero hallucination and draw.io export.',
      viewTab: 'architecture' as const,
    },
    {
      id: 'review_changes',
      title: 'Review Code Changes',
      icon: <GitBranch className="h-4 w-4 text-lime-accent" />,
      tag: 'Code Change Analyzer',
      prompt: 'Analyze git diff and AST structural impact across target_project with risk assessment.',
      desc: '10-step evidence-based change analysis, downstream impacts, and recommended pytest commands.',
      viewTab: 'change_review' as const,
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 py-8 max-w-3xl mx-auto">
      {/* Cockpit Icon Badge */}
      <div className="flex items-center gap-2 mb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-obsidian-subtle border border-obsidian-border text-lime-accent shadow-panel">
          <Terminal className="h-5 w-5" />
        </div>
        <div className="flex items-center gap-1.5 rounded-full border border-obsidian-border bg-obsidian-subtle px-2.5 py-1 text-[11px] font-mono text-cockpit-muted">
          <ShieldCheck className="h-3 w-3 text-lime-accent" />
          <span>target_project • Python 3.11</span>
        </div>
      </div>

      {/* Greeting Title */}
      <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-cockpit-text text-center mb-1">
        Multi-Agent Code Helper
      </h1>
      <div className="text-xs font-mono text-lime-accent uppercase tracking-wider mb-2">
        Code Helper AI — Obsidian Cockpit
      </div>
      <p className="text-cockpit-muted text-center max-w-xl text-xs sm:text-sm leading-relaxed mb-8">
        Ask anything about your Python codebase. Intelligent developer workspace backed by a five-agent Google ADK runtime, custom Pinecone RAG retrieval, Filesystem MCP, and a deterministic Python AST engine.
      </p>

      {/* 4 Starter Actions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
        {starterActions.map((action) => (
          <button
            key={action.id}
            onClick={() => {
              if (action.viewTab === 'chat' && onSelectPrompt) {
                onSelectPrompt(action.prompt);
              } else if (onNavigateTab) {
                onNavigateTab(action.viewTab);
              } else if (onSelectPrompt) {
                onSelectPrompt(action.prompt);
              }
            }}
            className="flex flex-col text-left rounded-xl border border-obsidian-border bg-obsidian-subtle p-4 transition-all hover:border-lime-accent/50 hover:bg-obsidian-elevated/80 group cursor-pointer"
          >
            <div className="flex items-center justify-between w-full mb-2">
              <div className="flex items-center gap-2 font-medium text-xs text-cockpit-text group-hover:text-lime-accent transition-colors">
                <span className="p-1.5 rounded-lg bg-obsidian-elevated border border-obsidian-border">
                  {action.icon}
                </span>
                <span>{action.title}</span>
              </div>
              <span className="rounded bg-obsidian-elevated px-2 py-0.5 font-mono text-[10px] text-cockpit-muted border border-obsidian-border">
                {action.tag}
              </span>
            </div>

            <p className="text-cockpit-muted text-[11px] leading-relaxed mb-3">
              {action.desc}
            </p>

            <div className="mt-auto pt-2 border-t border-obsidian-border/50 text-[11px] font-mono text-cockpit-faint group-hover:text-cockpit-muted transition-colors truncate">
              "{action.prompt}"
            </div>
          </button>
        ))}
      </div>

      {/* Bottom Hint */}
      <div className="mt-8 flex items-center gap-3 text-[11px] text-cockpit-faint">
        <span>Enter query below to route to Coordinator</span>
        <span>•</span>
        <span>Deterministic AST guarantees zero hallucination</span>
      </div>
    </div>
  );
};
