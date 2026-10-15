import React from 'react';
import {
  MessageSquare,
  FolderCode,
  Network,
  GitBranch,
  Plus,
  Terminal,
  X,
  CheckCircle2,
} from 'lucide-react';
import { SessionItem, HealthState, ActiveView } from '../types';

interface SidebarProps {
  sessions: SessionItem[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  health: HealthState;
  isOpen: boolean;
  onClose: () => void;
  activeView: ActiveView;
  onSelectView: (view: ActiveView) => void;
  onOpenDiagnostics: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  health,
  isOpen,
  onClose,
  activeView,
  onSelectView,
  onOpenDiagnostics,
}) => {
  const navItems: Array<{
    id: ActiveView;
    label: string;
    icon: React.ReactNode;
    tag?: string;
  }> = [
    {
      id: 'chat',
      label: 'Chat Workspace',
      icon: <MessageSquare className="h-4 w-4" />,
    },
    {
      id: 'explorer',
      label: 'Codebase Explorer',
      icon: <FolderCode className="h-4 w-4" />,
      tag: '5 files',
    },
    {
      id: 'architecture',
      label: 'Architecture Map',
      icon: <Network className="h-4 w-4" />,
      tag: 'AST',
    },
    {
      id: 'change_review',
      label: 'Change Review',
      icon: <GitBranch className="h-4 w-4" />,
      tag: 'Diff',
    },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs lg:hidden"
        />
      )}

      {/* Sidebar container (~256px) */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-obsidian-border bg-obsidian-bg transition-transform duration-200 lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header Branding */}
        <div className="flex items-center justify-between border-b border-obsidian-border px-4 py-3.5 bg-obsidian-subtle/80">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-obsidian-elevated border border-obsidian-border text-lime-accent shadow-panel">
              <Terminal className="h-4 w-4" />
            </div>
            <div>
              <h2 className="font-semibold text-xs text-cockpit-text tracking-tight uppercase">
                Code Helper AI
              </h2>
              <p className="text-[10px] text-cockpit-muted font-mono">Obsidian Cockpit</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-cockpit-muted hover:text-cockpit-text lg:hidden cursor-pointer"
            title="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Project Selector Box */}
        <div className="p-3 border-b border-obsidian-border/60 bg-obsidian-subtle/30">
          <div className="rounded-xl border border-obsidian-border bg-obsidian-subtle p-2.5 text-xs space-y-1">
            <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-cockpit-muted">
              <span>Active Project</span>
              <span className="flex items-center gap-1 text-lime-accent font-mono">
                <span className="h-1.5 w-1.5 rounded-full bg-lime-accent" />
                Indexed
              </span>
            </div>
            <div className="flex items-center justify-between pt-0.5">
              <div className="font-mono text-xs font-semibold text-cockpit-text flex items-center gap-1.5 truncate">
                <FolderCode className="h-3.5 w-3.5 text-cyan-source shrink-0" />
                <span className="truncate">target_project</span>
              </div>
              <span className="rounded bg-obsidian-elevated px-1.5 py-0.2 font-mono text-[10px] text-cockpit-faint border border-obsidian-border">
                main
              </span>
            </div>
          </div>
        </div>

        {/* Primary View Navigation */}
        <div className="px-3 pt-3 pb-2 space-y-1 border-b border-obsidian-border/60">
          <div className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-cockpit-muted">
            Workspace Views
          </div>
          {navItems.map((item) => {
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectView(item.id);
                  onClose();
                }}
                className={`flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-xs transition-colors cursor-pointer ${
                  isActive
                    ? 'bg-obsidian-elevated text-lime-accent font-medium border border-obsidian-border'
                    : 'text-cockpit-muted hover:bg-obsidian-subtle hover:text-cockpit-text'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={isActive ? 'text-lime-accent' : 'text-cockpit-muted'}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </div>
                {item.tag && (
                  <span className="rounded bg-obsidian-bg px-1.5 py-0.2 font-mono text-[10px] text-cockpit-faint border border-obsidian-border">
                    {item.tag}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={() => {
              onNewChat();
              onSelectView('chat');
              onClose();
            }}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-lime-accent/10 border border-lime-accent/40 hover:bg-lime-accent hover:text-obsidian-bg px-3 py-2 text-xs font-semibold text-lime-accent transition-all cursor-pointer shadow-sm group"
          >
            <Plus className="h-3.5 w-3.5 group-hover:stroke-[3]" />
            <span>New Conversation</span>
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1">
          <div className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-cockpit-muted">
            Recent Conversations
          </div>

          {sessions.length === 0 ? (
            <div className="px-3 py-3 text-center text-xs text-cockpit-faint">
              No recent conversations.
            </div>
          ) : (
            sessions.map((s) => {
              const isActive = s.sessionId === activeSessionId && activeView === 'chat';
              return (
                <button
                  key={s.sessionId}
                  onClick={() => {
                    onSelectSession(s.sessionId);
                    onSelectView('chat');
                    onClose();
                  }}
                  className={`flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-xs transition-colors cursor-pointer ${
                    isActive
                      ? 'bg-obsidian-elevated text-lime-accent font-medium border border-obsidian-border'
                      : 'text-cockpit-muted hover:bg-obsidian-subtle hover:text-cockpit-text'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <MessageSquare
                      className={`h-3.5 w-3.5 shrink-0 ${
                        isActive ? 'text-lime-accent' : 'text-cockpit-faint'
                      }`}
                    />
                    <span className="truncate">{s.title}</span>
                  </div>
                  {s.messageCount > 0 && (
                    <span className="shrink-0 rounded-full bg-obsidian-elevated px-1.5 py-0.2 font-mono text-[10px] text-cockpit-faint border border-obsidian-border">
                      {s.messageCount}
                    </span>
                  )}
                </button>
              );
            })
          )}
        </div>

        {/* Connected Services Section */}
        <div className="border-t border-obsidian-border p-3 bg-obsidian-subtle/40 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-cockpit-muted">
              Connected Services
            </span>
            {health.status === 'ok' ? (
              <span className="flex items-center gap-1 text-[10px] font-mono text-lime-accent">
                <CheckCircle2 className="h-3 w-3" />
                Services Connected
              </span>
            ) : (
              <button
                onClick={onOpenDiagnostics}
                className="text-[10px] text-cyan-source hover:underline font-mono cursor-pointer"
              >
                Diagnostics
              </button>
            )}
          </div>

          <div className="rounded-lg bg-obsidian-bg p-2.5 text-[11px] space-y-1.5 text-cockpit-muted border border-obsidian-border font-mono">
            {/* FastAPI Backend */}
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-cockpit-text">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    health.backendRunning ? 'bg-lime-accent' : 'bg-red-err'
                  }`}
                />
                FastAPI Backend
              </span>
              <span className={health.backendRunning ? 'text-lime-accent' : 'text-red-err'}>
                {health.backendRunning ? ':8001' : 'offline'}
              </span>
            </div>

            {/* Google ADK Runtime */}
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-cockpit-text">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    health.adkReachable ? 'bg-lime-accent' : 'bg-amber-warn'
                  }`}
                />
                Google ADK App
              </span>
              <span className={health.adkReachable ? 'text-lime-accent' : 'text-amber-warn'}>
                {health.adkReachable ? ':8000' : 'standby'}
              </span>
            </div>

            {/* Pinecone Vector DB */}
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-cockpit-text">
                <span className="h-1.5 w-1.5 rounded-full bg-lime-accent" />
                Pinecone Vector
              </span>
              <span className="text-lime-accent">ready</span>
            </div>

            {/* Filesystem MCP */}
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-cockpit-text">
                <span className="h-1.5 w-1.5 rounded-full bg-lime-accent" />
                Filesystem MCP
              </span>
              <span className="text-lime-accent">active</span>
            </div>

            {/* Draw.io MCP */}
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-cockpit-text">
                <span className="h-1.5 w-1.5 rounded-full bg-lime-accent" />
                Draw.io MCP
              </span>
              <span className="text-lime-accent">ready</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
