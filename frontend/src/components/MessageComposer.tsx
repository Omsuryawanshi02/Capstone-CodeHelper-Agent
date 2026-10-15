import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Square, AlertCircle, Sparkles } from 'lucide-react';

interface MessageComposerProps {
  onSend: (message: string) => void;
  onCancel: () => void;
  isStreaming: boolean;
  disabled?: boolean;
  error?: string | null;
  onClearError?: () => void;
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  onSend,
  onCancel,
  isStreaming,
  disabled,
  error,
  onClearError,
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (disabled || isStreaming) return;
    const trimmed = input.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 pb-4 pt-2">
      {/* Error alert banner */}
      {error && (
        <div className="mb-2.5 flex items-center justify-between rounded-lg border border-red-err/40 bg-red-err/10 px-3.5 py-2 text-xs text-red-err shadow-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-err" />
            <span className="font-mono text-[11px]">{error}</span>
          </div>
          {onClearError && (
            <button
              onClick={onClearError}
              className="text-red-err hover:underline text-xs font-semibold ml-2 cursor-pointer"
            >
              Dismiss
            </button>
          )}
        </div>
      )}

      {/* Input container */}
      <form
        onSubmit={handleSubmit}
        className="relative flex items-end rounded-xl border border-obsidian-border bg-obsidian-subtle shadow-panel transition-all focus-within:border-lime-accent/60 focus-within:ring-1 focus-within:ring-lime-accent/30 p-2"
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask where code is, what a file does, inspect imports, or review git changes..."
          rows={1}
          disabled={disabled}
          className="w-full resize-none bg-transparent px-3 py-2 text-xs sm:text-sm text-cockpit-text placeholder:text-cockpit-faint focus:outline-none max-h-40 disabled:opacity-50 font-sans"
        />

        <div className="flex items-center gap-2 pr-1 pb-1">
          {isStreaming ? (
            <button
              type="button"
              onClick={onCancel}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-obsidian-elevated text-red-err hover:bg-red-err/20 border border-obsidian-border transition-colors cursor-pointer"
              title="Stop streaming (Escape)"
            >
              <Square className="h-3.5 w-3.5 fill-current" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={disabled || !input.trim()}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-lime-accent text-obsidian-bg hover:bg-lime-hover disabled:opacity-30 disabled:hover:bg-lime-accent transition-all font-semibold shadow-sm cursor-pointer"
              title="Send message (Enter)"
            >
              <ArrowUp className="h-4 w-4 stroke-[2.5]" />
            </button>
          )}
        </div>
      </form>

      {/* Helper metadata bar */}
      <div className="mt-1.5 flex items-center justify-between text-[11px] text-cockpit-faint px-1">
        <div className="flex items-center gap-1.5">
          <span>Press</span>
          <kbd className="rounded border border-obsidian-border bg-obsidian-elevated px-1.5 py-0.2 font-mono text-[10px] text-cockpit-muted">
            Enter ↵
          </kbd>
          <span>to send</span>
          <span className="text-cockpit-faint">•</span>
          <kbd className="rounded border border-obsidian-border bg-obsidian-elevated px-1.5 py-0.2 font-mono text-[10px] text-cockpit-muted">
            Shift+Enter
          </kbd>
          <span>for newline</span>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 font-mono text-[10px] text-cockpit-muted">
          <Sparkles className="h-3 w-3 text-violet-ai" />
          <span>Coordinator • 4 Specialists</span>
        </div>
      </div>
    </div>
  );
};
