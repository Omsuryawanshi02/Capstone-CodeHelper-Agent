import React from 'react';
import { Plus, MessageSquare, Bot, CheckCircle2, AlertTriangle, XCircle, X } from 'lucide-react';
import { SessionItem, HealthState } from '../types';

interface SidebarProps {
  sessions: SessionItem[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  health: HealthState;
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  health,
  isOpen,
  onClose,
}) => {
  const getHealthBadge = () => {
    if (health.status === 'ok') {
      return (
        <div className="flex items-center gap-1.5 text-xs text-emerald-400">
          <CheckCircle2 className="h-3.5 w-3.5" />
          <span>Services Connected</span>
        </div>
      );
    }
    if (health.status === 'degraded') {
      return (
        <div className="flex items-center gap-1.5 text-xs text-amber-400" title="Check ADK server or API keys">
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>ADK Disconnected / Standby</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1.5 text-xs text-red-400">
        <XCircle className="h-3.5 w-3.5" />
        <span>Backend Offline</span>
      </div>
    );
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-800/80 bg-slate-950 transition-transform duration-200 lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header Branding */}
        <div className="flex items-center justify-between border-b border-slate-800/80 px-4 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-700 text-white shadow-md shadow-emerald-950/40">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-semibold text-sm text-slate-100 tracking-tight">Code Helper AI</h2>
              <p className="text-[11px] text-slate-400">Google ADK Multi-Agent</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-200 lg:hidden"
            title="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={onNewChat}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700/60 bg-slate-900/90 hover:bg-slate-850 px-4 py-2.5 text-xs font-semibold text-slate-200 shadow-sm transition-all hover:border-emerald-500/50 hover:text-white cursor-pointer"
          >
            <Plus className="h-4 w-4 text-emerald-400" />
            <span>New Conversation</span>
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          <div className="px-2 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Recent Conversations
          </div>

          {sessions.length === 0 ? (
            <div className="px-3 py-4 text-center text-xs text-slate-500">
              No recent conversations yet.
            </div>
          ) : (
            sessions.map((s) => {
              const isActive = s.sessionId === activeSessionId;
              return (
                <button
                  key={s.sessionId}
                  onClick={() => {
                    onSelectSession(s.sessionId);
                    onClose();
                  }}
                  className={`flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2.5 text-left text-xs transition-colors cursor-pointer ${
                    isActive
                      ? 'bg-slate-850 text-emerald-300 font-medium border border-slate-700/80'
                      : 'text-slate-300 hover:bg-slate-900/60 hover:text-slate-100'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <MessageSquare className={`h-3.5 w-3.5 shrink-0 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span className="truncate">{s.title}</span>
                  </div>
                  {s.messageCount > 0 && (
                    <span className="shrink-0 rounded-full bg-slate-800 px-1.5 py-0.2 font-mono text-[10px] text-slate-400">
                      {s.messageCount}
                    </span>
                  )}
                </button>
              );
            })
          )}
        </div>

        {/* Bottom System Status */}
        <div className="border-t border-slate-800/80 p-3 bg-slate-950/60 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Status</span>
            {getHealthBadge()}
          </div>
          <div className="rounded-lg bg-slate-900/70 p-2.5 text-[11px] space-y-1 text-slate-400 border border-slate-850">
            <div className="flex justify-between">
              <span>FastAPI Backend:</span>
              <span className={health.backendRunning ? 'text-emerald-400 font-mono' : 'text-red-400 font-mono'}>
                {health.backendRunning ? ':8001' : 'offline'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Google ADK API:</span>
              <span className={health.adkReachable ? 'text-emerald-400 font-mono' : 'text-amber-400 font-mono'}>
                {health.adkReachable ? ':8000' : 'standby'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Target Project:</span>
              <span className="text-slate-300 font-mono truncate">target_project</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
