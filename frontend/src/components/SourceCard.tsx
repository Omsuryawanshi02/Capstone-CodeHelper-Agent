import React, { useState } from 'react';
import { FileCode, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { SourceItem } from '../types';

interface SourceCardProps {
  source: SourceItem;
  onSelectFile?: (filePath: string) => void;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source, onSelectFile }) => {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const citation = `${source.filePath}${
    source.startLine && source.endLine ? `#L${source.startLine}-L${source.endLine}` : ''
  }`;

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(citation);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy source reference:', err);
    }
  };

  return (
    <div className="flex flex-col rounded-md border border-obsidian-border bg-obsidian-subtle/80 text-xs transition-all hover:border-cyan-source/50 group">
      <div className="flex items-center justify-between gap-2 p-2.5">
        <div
          onClick={() => onSelectFile && onSelectFile(source.filePath)}
          className="flex items-center gap-1.5 font-mono text-cyan-source font-medium truncate cursor-pointer hover:underline"
          title={`View ${source.filePath}`}
        >
          <FileCode className="h-3.5 w-3.5 shrink-0 text-cyan-source" />
          <span className="truncate">{source.filePath}</span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleCopy}
            className="p-1 text-cockpit-muted hover:text-cockpit-text transition-colors rounded hover:bg-obsidian-elevated cursor-pointer"
            title="Copy file path & line reference"
          >
            {copied ? <Check className="h-3 w-3 text-lime-accent" /> : <Copy className="h-3 w-3" />}
          </button>
          {source.snippet && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 text-cockpit-muted hover:text-cockpit-text transition-colors rounded hover:bg-obsidian-elevated cursor-pointer"
              title={expanded ? 'Collapse snippet' : 'Expand snippet'}
            >
              {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 px-2.5 pb-2 text-cockpit-muted text-[11px]">
        {source.startLine && source.endLine ? (
          <span className="rounded bg-obsidian-elevated px-1.5 py-0.5 font-mono text-cockpit-text border border-obsidian-border">
            Lines {source.startLine}–{source.endLine}
          </span>
        ) : null}

        {source.score !== undefined && source.score !== null ? (
          <span className="rounded bg-cyan-source/10 border border-cyan-source/30 px-1.5 py-0.5 text-cyan-source font-mono">
            score {(source.score * 100).toFixed(0)}%
          </span>
        ) : null}

        {source.type && (
          <span className="rounded bg-violet-ai/10 border border-violet-ai/30 px-1.5 py-0.5 text-violet-ai font-mono text-[10px] uppercase">
            {source.type}
          </span>
        )}
      </div>

      {source.snippet ? (
        <div
          onClick={() => setExpanded(!expanded)}
          className={`border-t border-obsidian-border bg-obsidian-bg/80 p-2.5 font-mono text-[11px] text-cockpit-text whitespace-pre overflow-x-auto cursor-pointer ${
            expanded ? '' : 'line-clamp-2'
          }`}
          title="Click to toggle full snippet"
        >
          {source.snippet}
        </div>
      ) : null}
    </div>
  );
};
