import React, { useState } from 'react';
import { FileCode, Copy, Check } from 'lucide-react';
import { SourceItem } from '../types';

interface SourceCardProps {
  source: SourceItem;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const citation = `${source.filePath}${
      source.startLine && source.endLine ? `#L${source.startLine}-L${source.endLine}` : ''
    }`;
    try {
      await navigator.clipboard.writeText(citation);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy source reference:', err);
    }
  };

  return (
    <div className="flex flex-col gap-1.5 rounded-md border border-slate-800 bg-slate-900/60 p-3 text-xs transition-colors hover:border-slate-700">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 font-mono text-emerald-400 font-medium truncate">
          <FileCode className="h-4 w-4 shrink-0 text-emerald-500" />
          <span className="truncate" title={source.filePath}>{source.filePath}</span>
        </div>
        <button
          onClick={handleCopy}
          className="p-1 text-slate-400 hover:text-slate-200 transition-colors"
          title="Copy file path"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
      </div>

      <div className="flex items-center gap-2 text-slate-400">
        {source.startLine && source.endLine ? (
          <span className="rounded bg-slate-800/80 px-1.5 py-0.5 font-mono text-[11px] text-slate-300">
            Lines {source.startLine}–{source.endLine}
          </span>
        ) : null}
        {source.score !== undefined && source.score !== null ? (
          <span className="rounded bg-emerald-950/60 border border-emerald-800/40 px-1.5 py-0.5 text-[11px] text-emerald-300 font-mono">
            score {(source.score * 100).toFixed(0)}%
          </span>
        ) : null}
      </div>

      {source.snippet ? (
        <div className="mt-1 font-mono text-[11px] text-slate-400 bg-slate-950/50 p-2 rounded border border-slate-900/80 line-clamp-2">
          {source.snippet}
        </div>
      ) : null}
    </div>
  );
};
