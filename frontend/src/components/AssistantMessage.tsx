import React, { useState } from 'react';
import { Copy, Check, Sparkles, AlertTriangle, ArrowRight, ShieldCheck, HelpCircle } from 'lucide-react';
import { ChatMessage } from '../types';
import { MarkdownContent } from './MarkdownContent';
import { SourceCard } from './SourceCard';
import { AgentActivity } from './AgentActivity';

interface AssistantMessageProps {
  message: ChatMessage;
  onSelectAction?: (actionPrompt: string) => void;
  onSelectFile?: (filePath: string) => void;
}

export const AssistantMessage: React.FC<AssistantMessageProps> = ({
  message,
  onSelectAction,
  onSelectFile,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyAll = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  const structured = message.structuredAnswer;

  return (
    <div className="flex w-full justify-start py-3">
      <div className="flex max-w-[96%] sm:max-w-[90%] items-start gap-3">
        {/* Assistant Avatar */}
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-obsidian-elevated text-violet-ai border border-obsidian-border shadow-sm mt-0.5">
          <Sparkles className="h-3.5 w-3.5" />
        </div>

        <div className="flex-1 space-y-3 overflow-hidden">
          {/* Agent Activity Header (Dynamic Event Status) */}
          {(message.isStreaming || message.activity) && (
            <AgentActivity
              agentName={message.agentName}
              activity={message.activity}
              isComplete={!message.isStreaming}
            />
          )}

          {/* Structured Conclusion Card (if present) */}
          {structured?.conclusion && (
            <div className="rounded-xl border border-lime-accent/30 bg-obsidian-subtle p-3.5 shadow-sm">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-lime-accent flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Direct Conclusion
                </span>
                {structured.confidence && (
                  <span
                    className={`rounded px-1.5 py-0.2 font-mono text-[10px] uppercase border ${
                      structured.confidence === 'Confirmed'
                        ? 'border-lime-accent/40 bg-lime-accent/10 text-lime-accent'
                        : structured.confidence === 'Likely'
                        ? 'border-cyan-source/40 bg-cyan-source/10 text-cyan-source'
                        : 'border-amber-warn/40 bg-amber-warn/10 text-amber-warn'
                    }`}
                  >
                    [{structured.confidence}]
                  </span>
                )}
              </div>
              <p className="text-xs text-cockpit-text leading-relaxed font-medium">
                {structured.conclusion}
              </p>
            </div>
          )}

          {/* Main Markdown Content / Technical Explanation */}
          <div className="rounded-xl rounded-tl-none border border-obsidian-border bg-obsidian-subtle/70 p-4 sm:p-5 shadow-sm">
            {message.content ? (
              <MarkdownContent content={message.content} />
            ) : message.isStreaming ? (
              <div className="flex items-center gap-2 text-xs text-cockpit-muted italic">
                <span className="h-2 w-2 rounded-full bg-violet-ai animate-ping" />
                <span>Coordinating Google ADK agents & querying Pinecone...</span>
              </div>
            ) : null}

            {/* In-stream typing cursor */}
            {message.isStreaming && (
              <span className="inline-block h-3.5 w-1.5 ml-1 bg-lime-accent animate-pulse align-middle" />
            )}
          </div>

          {/* Verified Source References */}
          {message.sources && message.sources.length > 0 ? (
            <div className="space-y-2 pt-1">
              <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-cockpit-muted">
                <span>Verified Source References ({message.sources.length})</span>
                <span className="text-[10px] font-mono text-cyan-source font-normal">
                  Pinecone Vector & Filesystem MCP
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {message.sources.map((src, i) => (
                  <SourceCard
                    key={`${src.filePath}-${src.startLine}-${i}`}
                    source={src}
                    onSelectFile={onSelectFile}
                  />
                ))}
              </div>
            </div>
          ) : !message.isStreaming && message.content ? (
            <div className="flex items-center gap-1.5 rounded-md border border-obsidian-border bg-obsidian-subtle/50 px-3 py-1.5 text-[11px] text-cockpit-faint">
              <HelpCircle className="h-3 w-3" />
              <span>Evidence note: No direct repository source citations were returned for this query.</span>
            </div>
          ) : null}

          {/* Limitations Callout (Amber warning style) */}
          {structured?.limitations && (
            <div className="flex items-start gap-2.5 rounded-lg border border-amber-warn/40 bg-amber-warn/5 p-3 text-xs text-amber-warn">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block mb-0.5 text-[11px] uppercase tracking-wider">
                  Operational Limitations & Caveats
                </span>
                <span className="text-cockpit-muted text-[11px] leading-relaxed">
                  {structured.limitations}
                </span>
              </div>
            </div>
          )}

          {/* Relevant Next Actions (Clickable Prompts) */}
          {structured?.nextActions && structured.nextActions.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
                Suggested Next Actions
              </div>
              <div className="flex flex-wrap gap-1.5">
                {structured.nextActions.map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSelectAction && onSelectAction(action)}
                    className="flex items-center gap-1.5 rounded-lg border border-obsidian-border bg-obsidian-subtle px-2.5 py-1 text-xs text-cockpit-muted hover:border-lime-accent/50 hover:text-cockpit-text hover:bg-obsidian-elevated transition-colors cursor-pointer"
                  >
                    <ArrowRight className="h-3 w-3 text-lime-accent" />
                    <span>{action}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Bottom Action Toolbar */}
          {message.content && !message.isStreaming && (
            <div className="flex items-center justify-between text-xs text-cockpit-muted pt-1">
              <div className="flex items-center gap-3">
                <button
                  onClick={handleCopyAll}
                  className="flex items-center gap-1 text-[11px] text-cockpit-muted hover:text-cockpit-text transition-colors cursor-pointer"
                  title="Copy complete answer"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3 text-lime-accent" />
                      <span className="text-lime-accent">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      <span>Copy answer</span>
                    </>
                  )}
                </button>
              </div>

              <div className="text-[10px] font-mono text-cockpit-faint">
                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
