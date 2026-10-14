import React from 'react';
import { CodeBlock } from './CodeBlock';

interface MarkdownContentProps {
  content: string;
}

export const MarkdownContent: React.FC<MarkdownContentProps> = ({ content }) => {
  // Split into code blocks and normal markdown segments
  const parts: React.ReactNode[] = [];
  const codeBlockRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    const textBefore = content.slice(lastIndex, match.index);
    if (textBefore) {
      parts.push(renderTextMarkdown(textBefore, `text-${lastIndex}`));
    }

    const language = match[1] || 'python';
    const code = match[2];
    parts.push(<CodeBlock key={`code-${match.index}`} language={language} code={code} />);

    lastIndex = match.index + match[0].length;
  }

  const remaining = content.slice(lastIndex);
  if (remaining) {
    parts.push(renderTextMarkdown(remaining, `text-${lastIndex}`));
  }

  return <div className="space-y-2 text-slate-200 leading-relaxed text-[14.5px]">{parts}</div>;
};

function renderTextMarkdown(text: string, keyPrefix: string): React.ReactNode {
  const lines = text.split('\n');
  return (
    <div key={keyPrefix} className="space-y-1.5">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={`${keyPrefix}-blank-${idx}`} className="h-2" />;
        }

        // Headings
        if (trimmed.startsWith('### ')) {
          return (
            <h3 key={`${keyPrefix}-h3-${idx}`} className="text-base font-semibold text-slate-100 mt-3 mb-1">
              {renderInlineStyles(trimmed.slice(4))}
            </h3>
          );
        }
        if (trimmed.startsWith('## ')) {
          return (
            <h2 key={`${keyPrefix}-h2-${idx}`} className="text-lg font-bold text-slate-100 mt-4 mb-1">
              {renderInlineStyles(trimmed.slice(3))}
            </h2>
          );
        }
        if (trimmed.startsWith('# ')) {
          return (
            <h1 key={`${keyPrefix}-h1-${idx}`} className="text-xl font-bold text-slate-100 mt-4 mb-2">
              {renderInlineStyles(trimmed.slice(2))}
            </h1>
          );
        }

        // Bullet list
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <div key={`${keyPrefix}-li-${idx}`} className="flex items-start gap-2 pl-2">
              <span className="text-emerald-500 font-bold">•</span>
              <span className="flex-1">{renderInlineStyles(trimmed.slice(2))}</span>
            </div>
          );
        }

        // Numbered list
        const numMatch = trimmed.match(/^([0-9]+)\.\s+(.*)$/);
        if (numMatch) {
          return (
            <div key={`${keyPrefix}-num-${idx}`} className="flex items-start gap-2 pl-2">
              <span className="text-emerald-500 font-mono text-xs mt-0.5">{numMatch[1]}.</span>
              <span className="flex-1">{renderInlineStyles(numMatch[2])}</span>
            </div>
          );
        }

        // Standard paragraph line
        return <p key={`${keyPrefix}-p-${idx}`}>{renderInlineStyles(line)}</p>;
      })}
    </div>
  );
}

function renderInlineStyles(text: string): React.ReactNode[] {
  // Parse inline code `code` and bold **bold**
  const tokens: React.ReactNode[] = [];
  const regex = /(`[^`]+`|\*\*[^*]+\*\*)/g;

  let lastIdx = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      tokens.push(text.slice(lastIdx, match.index));
    }

    const token = match[0];
    if (token.startsWith('`') && token.endsWith('`')) {
      tokens.push(
        <code
          key={`inline-code-${match.index}`}
          className="rounded bg-slate-800/90 border border-slate-700/60 px-1.5 py-0.5 font-mono text-xs text-emerald-300"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith('**') && token.endsWith('**')) {
      tokens.push(
        <strong key={`bold-${match.index}`} className="font-semibold text-slate-100">
          {token.slice(2, -2)}
        </strong>
      );
    }

    lastIdx = match.index + token.length;
  }

  if (lastIdx < text.length) {
    tokens.push(text.slice(lastIdx));
  }

  return tokens;
}
