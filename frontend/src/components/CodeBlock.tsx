import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CodeBlockProps {
  language?: string;
  code: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ language, code }) => {
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

  return (
    <div className="relative my-3 rounded-lg border border-slate-800 bg-slate-900/90 overflow-hidden font-mono text-sm shadow-md">
      <div className="flex items-center justify-between border-b border-slate-800/80 bg-slate-950/60 px-3.5 py-1.5 text-xs text-slate-400">
        <span className="font-semibold text-slate-300">{language || 'code'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded px-2 py-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-emerald-400 text-xs">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span className="text-xs">Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="overflow-x-auto p-4 leading-relaxed text-slate-200">
        <pre>
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
};
