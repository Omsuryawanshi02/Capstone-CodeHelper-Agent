import React, { useState } from 'react';
import { Menu, FolderCode, Layers, Copy, Check } from 'lucide-react';
import { HealthState } from '../types';

interface ChatHeaderProps {
  onToggleSidebar: () => void;
  activeSessionId: string | null;
  health: HealthState;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  onToggleSidebar,
  activeSessionId,
  health,
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

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-4 sm:px-6 backdrop-blur shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-900 hover:text-slate-200 lg:hidden cursor-pointer"
          title="Toggle sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm text-slate-100 hidden sm:inline">Code Helper AI</span>
          <span className="text-slate-600 hidden sm:inline">•</span>
          <div className="flex items-center gap-1.5 rounded-md border border-slate-800 bg-slate-900/60 px-2 py-1 text-xs text-slate-300 font-mono">
            <FolderCode className="h-3.5 w-3.5 text-emerald-400" />
            <span>target_project</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        {/* Agent architecture badge */}
        <div className="hidden md:flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/60 px-2.5 py-1 text-xs text-slate-400">
          <Layers className="h-3.5 w-3.5 text-emerald-400" />
          <span>Coordinator + 4 Specialists</span>
        </div>

        {/* Live service health pill */}
        <div className="flex items-center gap-1 rounded-full border border-slate-800 bg-slate-900/40 px-2 py-0.5 text-[11px] text-slate-400">
          <span className={`inline-block h-2 w-2 rounded-full ${health.status === 'ok' ? 'bg-emerald-400' : health.status === 'degraded' ? 'bg-amber-400' : 'bg-red-400'}`} />
          <span className="hidden sm:inline capitalize">{health.status === 'ok' ? 'Ready' : health.status}</span>
        </div>

        {/* Session ID chip */}
        {activeSessionId && (
          <button
            onClick={handleCopySessionId}
            className="flex items-center gap-1.5 rounded-md border border-slate-800/80 bg-slate-900/40 px-2 py-1 text-[11px] font-mono text-slate-400 hover:bg-slate-850 hover:text-slate-300 transition-colors cursor-pointer"
            title="Click to copy Session ID"
          >
            <span>Session:</span>
            <span className="text-slate-300">{activeSessionId.slice(0, 8)}...</span>
            {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
          </button>
        )}
      </div>
    </header>
  );
};
