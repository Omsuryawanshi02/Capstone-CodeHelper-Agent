import React, { useState } from 'react';
import { Copy, Check, Terminal } from 'lucide-react';

interface CodeBlockProps {
  language?: string;
  filename?: string;
  lineRange?: string;
  code: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  language = 'python',
  filename,
  lineRange,
  code,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  const lines = code.trim().split('\n');

  return (
    <div className="relative my-3 rounded-lg border border-obsidian-border bg-obsidian-bg overflow-hidden font-mono text-xs shadow-md">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between border-b border-obsidian-border bg-obsidian-subtle px-3.5 py-1.5 text-cockpit-muted">
        <div className="flex items-center gap-2">
          <Terminal className="h-3.5 w-3.5 text-lime-accent" />
          {filename ? (
            <span className="font-semibold text-cockpit-text">{filename}</span>
          ) : (
            <span className="font-medium text-cockpit-muted uppercase tracking-wider text-[10px]">
              {language}
            </span>
          )}
          {lineRange && (
            <span className="rounded bg-obsidian-elevated px-1.5 py-0.5 text-[10px] text-cyan-source border border-obsidian-border">
              {lineRange}
            </span>
          )}
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] text-cockpit-muted hover:bg-obsidian-elevated hover:text-cockpit-text transition-colors cursor-pointer"
          title="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-lime-accent" />
              <span className="text-lime-accent">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Content with Line Numbers */}
      <div className="overflow-x-auto p-3.5 leading-relaxed text-cockpit-text bg-obsidian-bg/95">
        <table className="border-collapse w-full">
          <tbody>
            {lines.map((line, idx) => (
              <tr key={idx} className="hover:bg-obsidian-elevated/40 transition-colors">
                <td className="code-line-number text-[11px] pr-3 select-none text-cockpit-faint text-right w-8">
                  {idx + 1}
                </td>
                <td className="pl-2 font-mono whitespace-pre text-[12px] text-cockpit-text">
                  {line || ' '}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
