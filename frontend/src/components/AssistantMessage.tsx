import React, { useState } from 'react';
import { Copy, Check, Sparkles } from 'lucide-react';
import { ChatMessage } from '../types';
import { MarkdownContent } from './MarkdownContent';
import { SourceCard } from './SourceCard';
import { AgentActivity } from './AgentActivity';

interface AssistantMessageProps {
  message: ChatMessage;
}

export const AssistantMessage: React.FC<AssistantMessageProps> = ({ message }) => {
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

  return (
    <div className="flex w-full justify-start py-3">
      <div className="flex max-w-[95%] sm:max-w-[88%] items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-800 text-emerald-400 border border-slate-700 shadow-sm mt-0.5">
          <Sparkles className="h-4 w-4" />
        </div>

        <div className="flex-1 space-y-3 overflow-hidden">
          {/* Agent Activity Indicator */}
          {(message.isStreaming || message.activity) && (
            <AgentActivity agentName={message.agentName} activity={message.activity} />
          )}

          {/* Response Text */}
          <div className="rounded-2xl rounded-tl-none border border-slate-800/80 bg-slate-900/40 p-4 sm:p-5 shadow-sm">
            {message.content ? (
              <MarkdownContent content={message.content} />
            ) : message.isStreaming ? (
              <span className="inline-flex items-center gap-1.5 text-sm text-slate-400 italic">
                Reasoning across multi-agent system...
              </span>
            ) : null}

            {/* In-stream typing cursor */}
            {message.isStreaming && (
              <span className="inline-block h-4 w-2 ml-1 bg-emerald-400 animate-pulse align-middle" />
            )}
          </div>

          {/* Grounded Source References */}
          {message.sources && message.sources.length > 0 && (
            <div className="space-y-2 pt-1">
              <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <span>Verified Source References ({message.sources.length})</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {message.sources.map((src, i) => (
                  <SourceCard key={`${src.filePath}-${src.startLine}-${i}`} source={src} />
                ))}
              </div>
            </div>
          )}

          {/* Action toolbar */}
          {message.content && !message.isStreaming && (
            <div className="flex items-center gap-2 pl-1 pt-0.5">
              <button
                onClick={handleCopyAll}
                className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                title="Copy entire answer"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>Copy answer</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
