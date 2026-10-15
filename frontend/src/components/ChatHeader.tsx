import React, { useState } from 'react';
import {
  Menu,
  FolderCode,
  Copy,
  Check,
  PanelRight,
  Cpu,
} from 'lucide-react';
import { HealthState, ActiveView } from '../types';

interface ChatHeaderProps {
  onToggleSidebar: () => void;
  activeSessionId: string | null;
  health: HealthState;
  activeView: ActiveView;
  onSelectView?: (view: ActiveView) => void;
  isRightPanelOpen: boolean;
  onToggleRightPanel: () => void;
  onOpenDiagnostics: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  onToggleSidebar,
  activeSessionId,
  health,
  activeView,
  isRightPanelOpen,
  onToggleRightPanel,
  onOpenDiagnostics,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopySessionId = async () => {
    if (!activeSessionId) return;
    try {
      await navigator.clipboard.writeText(activeSessionId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy session ID:', err);
    }
  };

  const getViewTitle = () => {
    switch (activeView) {
      case 'explorer':
        return 'Codebase Explorer';
      case 'architecture':
        return 'Architecture Dependency Map';
      case 'change_review':
        return 'Code Change Review';
      default:
        return 'Chat Workspace';
    }
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-obsidian-border bg-obsidian-subtle/80 px-4 sm:px-6 backdrop-blur-xs shrink-0 select-none">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="rounded-lg p-1.5 text-cockpit-muted hover:bg-obsidian-elevated hover:text-cockpit-text lg:hidden cursor-pointer"
          title="Toggle sidebar"
        >
          <Menu className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="flex items-center gap-1.5 rounded-lg border border-obsidian-border bg-obsidian-elevated px-2 py-1 text-cockpit-text">
            <FolderCode className="h-3.5 w-3.5 text-lime-accent" />
            <span className="font-semibold">target_project</span>
          </div>

          <span className="text-cockpit-faint hidden sm:inline">•</span>

          <span className="text-cockpit-muted hidden sm:inline">
            {getViewTitle()}
          </span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Architecture Badge */}
        <div className="hidden lg:flex items-center gap-1.5 rounded-full border border-obsidian-border bg-obsidian-subtle px-2.5 py-1 text-xs text-cockpit-muted font-mono">
          <Cpu className="h-3.5 w-3.5 text-violet-ai" />
          <span>Google ADK (5 Agents)</span>
        </div>

        {/* Live Service Diagnostics Status Button */}
        <button
          onClick={onOpenDiagnostics}
          className="flex items-center gap-1.5 rounded-full border border-obsidian-border bg-obsidian-subtle px-2.5 py-1 text-xs text-cockpit-muted hover:border-lime-accent/50 hover:text-cockpit-text transition-colors cursor-pointer"
          title="Open Service & Error Diagnostics (Screen F)"
        >
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              health.status === 'ok'
                ? 'bg-lime-accent'
                : health.status === 'degraded'
                ? 'bg-amber-warn'
                : 'bg-red-err'
            }`}
          />
          <span className="hidden md:inline font-mono text-[11px] capitalize">
            {health.status === 'ok' ? 'Services Ready' : health.status}
          </span>
        </button>

        {/* Active Session Token */}
        {activeSessionId && activeView === 'chat' && (
          <button
            onClick={handleCopySessionId}
            className="hidden sm:flex items-center gap-1.5 rounded-lg border border-obsidian-border bg-obsidian-subtle px-2.5 py-1 text-[11px] font-mono text-cockpit-muted hover:bg-obsidian-elevated hover:text-cockpit-text transition-colors cursor-pointer"
            title="Click to copy Session ID"
          >
            <span>Session:</span>
            <span className="text-cockpit-text font-semibold">
              {activeSessionId.slice(0, 8)}...
            </span>
            {copied ? (
              <Check className="h-3 w-3 text-lime-accent" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </button>
        )}

        {/* Toggle Right Context Inspector */}
        <button
          onClick={onToggleRightPanel}
          className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer ${
            isRightPanelOpen
              ? 'border-cyan-source/50 bg-cyan-source/10 text-cyan-source'
              : 'border-obsidian-border bg-obsidian-subtle text-cockpit-muted hover:text-cockpit-text hover:bg-obsidian-elevated'
          }`}
          title={isRightPanelOpen ? 'Hide Context Inspector' : 'Show Context Inspector'}
        >
          <PanelRight className="h-4 w-4" />
          <span className="hidden sm:inline">Inspector</span>
        </button>
      </div>
    </header>
  );
};
