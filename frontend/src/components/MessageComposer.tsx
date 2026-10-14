import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Square, AlertCircle } from 'lucide-react';

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
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 pb-6 pt-2">
      {/* Error alert banner */}
      {error && (
        <div className="mb-3 flex items-center justify-between rounded-lg border border-red-800/60 bg-red-950/40 px-3.5 py-2 text-xs text-red-300">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
          {onClearError && (
            <button
              onClick={onClearError}
              className="text-red-400 hover:text-red-200 text-xs underline font-medium ml-2 cursor-pointer"
            >
              Dismiss
            </button>
          )}
        </div>
      )}

      {/* Input container */}
      <form
        onSubmit={handleSubmit}
        className="relative flex items-end rounded-2xl border border-slate-800 bg-slate-900/90 shadow-xl transition-all focus-within:border-emerald-500/70 focus-within:ring-1 focus-within:ring-emerald-500/30 p-2"
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask where code is, what a file does, import connections, or setup instructions..."
          rows={1}
          disabled={disabled}
          className="w-full resize-none bg-transparent px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none max-h-44 disabled:opacity-50"
        />

        <div className="flex items-center gap-2 pr-1 pb-1">
          {isStreaming ? (
            <button
              type="button"
              onClick={onCancel}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors cursor-pointer"
              title="Stop generating"
            >
              <Square className="h-4 w-4 fill-current text-red-400" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={disabled || !input.trim()}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-30 disabled:hover:bg-emerald-600 transition-colors cursor-pointer"
              title="Send message (Enter)"
            >
              <ArrowUp className="h-4 w-4" />
            </button>
          )}
        </div>
      </form>
      <div className="mt-1.5 flex items-center justify-between text-[11px] text-slate-500 px-2">
        <span>Press <kbd className="font-mono text-slate-400">Enter</kbd> to send, <kbd className="font-mono text-slate-400">Shift+Enter</kbd> for newline</span>
        <span className="hidden sm:inline">Google ADK Multi-Agent Architecture</span>
      </div>
    </div>
  );
};
