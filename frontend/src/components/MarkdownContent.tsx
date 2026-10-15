import React from 'react';
import { CodeBlock } from './CodeBlock';

interface MarkdownContentProps {
  content: string;
}

export const MarkdownContent: React.FC<MarkdownContentProps> = ({ content }) => {
  // Split into code blocks and normal markdown segments
  const parts: React.ReactNode[] = [];
  // Regex to extract language and optional filename comments like ```python:target_project/query_pipeline.py
  const codeBlockRegex = /```([a-zA-Z0-9_\-\.\/]*)\n([\s\S]*?)```/g;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    const textBefore = content.slice(lastIndex, match.index);
    if (textBefore) {
      parts.push(renderTextMarkdown(textBefore, `text-${lastIndex}`));
    }

    const header = match[1] || 'python';
    let language = 'python';
    let filename: string | undefined = undefined;

    if (header.includes(':')) {
      const split = header.split(':');
      language = split[0];
      filename = split[1];
    } else {
      language = header;
    }

    const code = match[2];
    parts.push(
      <CodeBlock
        key={`code-${match.index}`}
        language={language}
        filename={filename}
        code={code}
      />
    );

    lastIndex = match.index + match[0].length;
  }

  const remaining = content.slice(lastIndex);
  if (remaining) {
    parts.push(renderTextMarkdown(remaining, `text-${lastIndex}`));
  }

  return <div className="space-y-2 text-cockpit-text leading-relaxed text-[13.5px]">{parts}</div>;
};

function renderTextMarkdown(text: string, keyPrefix: string): React.ReactNode {
  const lines = text.split('\n');
  return (
    <div key={keyPrefix} className="space-y-1.5">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={`${keyPrefix}-blank-${idx}`} className="h-1.5" />;
        }

        // Headings
        if (trimmed.startsWith('### ')) {
          return (
            <h3 key={`${keyPrefix}-h3-${idx}`} className="text-sm font-semibold text-cockpit-text mt-3 mb-1 tracking-tight">
              {renderInlineStyles(trimmed.slice(4))}
            </h3>
          );
        }
        if (trimmed.startsWith('## ')) {
          return (
            <h2 key={`${keyPrefix}-h2-${idx}`} className="text-base font-semibold text-cockpit-text mt-3.5 mb-1 tracking-tight">
              {renderInlineStyles(trimmed.slice(3))}
            </h2>
          );
        }
        if (trimmed.startsWith('# ')) {
          return (
            <h1 key={`${keyPrefix}-h1-${idx}`} className="text-lg font-bold text-cockpit-text mt-4 mb-2 tracking-tight">
              {renderInlineStyles(trimmed.slice(2))}
            </h1>
          );
        }

        // Bullet list
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <div key={`${keyPrefix}-li-${idx}`} className="flex items-start gap-2 pl-2 text-cockpit-text">
              <span className="text-lime-accent font-bold leading-5">•</span>
              <span className="flex-1">{renderInlineStyles(trimmed.slice(2))}</span>
            </div>
          );
        }

        // Numbered list
        const numMatch = trimmed.match(/^([0-9]+)\.\s+(.*)$/);
        if (numMatch) {
          return (
            <div key={`${keyPrefix}-num-${idx}`} className="flex items-start gap-2 pl-2 text-cockpit-text">
              <span className="text-lime-accent font-mono text-xs mt-0.5">{numMatch[1]}.</span>
              <span className="flex-1">{renderInlineStyles(numMatch[2])}</span>
            </div>
          );
        }

        // Standard paragraph line
        return (
          <p key={`${keyPrefix}-p-${idx}`} className="text-cockpit-text leading-relaxed">
            {renderInlineStyles(line)}
          </p>
        );
      })}
    </div>
  );
}

function renderInlineStyles(text: string): React.ReactNode[] {
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
          className="rounded bg-obsidian-elevated border border-obsidian-border px-1.5 py-0.5 font-mono text-[11.5px] text-lime-accent"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith('**') && token.endsWith('**')) {
      tokens.push(
        <strong key={`bold-${match.index}`} className="font-semibold text-cockpit-text">
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
