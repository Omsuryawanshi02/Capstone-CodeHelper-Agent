import React, { useState, useMemo } from 'react';
import {
  Folder,
  FileCode,
  Search,
  MessageSquare,
  Copy,
  Check,
  ChevronRight,
  ShieldCheck,
  Code2,
  Box,
  Layers,
} from 'lucide-react';
import { TARGET_PROJECT_FILES } from '../data/projectData';
import { CodeBlock } from './CodeBlock';

interface CodebaseExplorerProps {
  onAskAboutFile: (prompt: string) => void;
  initialSelectedPath?: string;
}

export const CodebaseExplorer: React.FC<CodebaseExplorerProps> = ({
  onAskAboutFile,
  initialSelectedPath,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPath, setSelectedPath] = useState<string>(
    initialSelectedPath || TARGET_PROJECT_FILES[0].path
  );
  const [copiedPath, setCopiedPath] = useState(false);

  const filteredFiles = useMemo(() => {
    if (!searchQuery.trim()) return TARGET_PROJECT_FILES;
    const q = searchQuery.toLowerCase();
    return TARGET_PROJECT_FILES.filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        f.path.toLowerCase().includes(q) ||
        f.imports.some((i) => i.toLowerCase().includes(q))
    );
  }, [searchQuery]);

  const activeFile = useMemo(() => {
    return (
      TARGET_PROJECT_FILES.find((f) => f.path === selectedPath) ||
      TARGET_PROJECT_FILES[0]
    );
  }, [selectedPath]);

  const handleCopyPath = async () => {
    try {
      await navigator.clipboard.writeText(activeFile.path);
      setCopiedPath(true);
      setTimeout(() => setCopiedPath(false), 2000);
    } catch (err) {
      console.error('Failed to copy path:', err);
    }
  };

  return (
    <div className="flex flex-1 h-full min-w-0 bg-obsidian-bg overflow-hidden flex-col md:flex-row">
      {/* Left File Tree Sidebar (~280px) */}
      <div className="flex w-full md:w-72 flex-col border-b md:border-b-0 md:border-r border-obsidian-border bg-obsidian-subtle/50 shrink-0">
        {/* Search header */}
        <div className="p-3 border-b border-obsidian-border bg-obsidian-subtle/80">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-cockpit-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search files or imports..."
              className="w-full rounded-lg border border-obsidian-border bg-obsidian-bg pl-8 pr-3 py-1.5 text-xs text-cockpit-text placeholder:text-cockpit-faint focus:border-lime-accent/50 focus:outline-none font-mono"
            />
          </div>
        </div>

        {/* Directory Header */}
        <div className="flex items-center justify-between px-3.5 py-2 text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted border-b border-obsidian-border/50">
          <div className="flex items-center gap-1.5">
            <Folder className="h-3.5 w-3.5 text-lime-accent" />
            <span>target_project</span>
          </div>
          <span className="font-mono text-[10px] text-cockpit-faint">
            {filteredFiles.length} files
          </span>
        </div>

        {/* File List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {filteredFiles.map((file) => {
            const isSelected = file.path === activeFile.path;
            return (
              <button
                key={file.path}
                onClick={() => setSelectedPath(file.path)}
                className={`flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-xs transition-colors cursor-pointer ${
                  isSelected
                    ? 'bg-obsidian-elevated text-lime-accent font-medium border border-obsidian-border'
                    : 'text-cockpit-muted hover:bg-obsidian-subtle hover:text-cockpit-text'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <FileCode
                    className={`h-3.5 w-3.5 shrink-0 ${
                      isSelected ? 'text-lime-accent' : 'text-cyan-source'
                    }`}
                  />
                  <span className="truncate font-mono">{file.name}</span>
                </div>

                <div className="flex items-center gap-1.5 font-mono text-[10px] text-cockpit-faint shrink-0">
                  <span>{file.lineCount}L</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Quick project stats footer */}
        <div className="border-t border-obsidian-border p-3 text-[11px] font-mono text-cockpit-muted space-y-1 bg-obsidian-bg">
          <div className="flex justify-between">
            <span>Total Lines:</span>
            <span className="text-cockpit-text">407 lines</span>
          </div>
          <div className="flex justify-between">
            <span>Runtime:</span>
            <span className="text-cyan-source">Python 3.11</span>
          </div>
          <div className="flex justify-between">
            <span>AST Parse:</span>
            <span className="text-lime-accent">100% Deterministic</span>
          </div>
        </div>
      </div>

      {/* Main File Preview and Inspector Area */}
      <div className="flex flex-1 flex-col h-full min-w-0 overflow-hidden bg-obsidian-bg">
        {/* Breadcrumb & Action Bar */}
        <div className="flex flex-wrap items-center justify-between border-b border-obsidian-border bg-obsidian-subtle/80 px-4 py-2.5 gap-2 shrink-0">
          <div className="flex items-center gap-1.5 font-mono text-xs text-cockpit-muted truncate">
            <span>target_project</span>
            <ChevronRight className="h-3 w-3 text-cockpit-faint" />
            <span className="text-cockpit-text font-semibold">{activeFile.name}</span>

            <button
              onClick={handleCopyPath}
              className="p-1 text-cockpit-muted hover:text-cockpit-text ml-1 rounded hover:bg-obsidian-elevated cursor-pointer"
              title="Copy relative file path"
            >
              {copiedPath ? (
                <Check className="h-3 w-3 text-lime-accent" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </button>
          </div>

          {/* Ask Assistant About This File Button */}
          <button
            onClick={() =>
              onAskAboutFile(
                `Explain ${activeFile.path}, its key functions, imports, and downstream dependencies in target_project.`
              )
            }
            className="flex items-center gap-1.5 rounded-lg bg-lime-accent px-3 py-1.5 text-xs font-semibold text-obsidian-bg hover:bg-lime-hover transition-colors shadow-sm cursor-pointer"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Ask Assistant About File</span>
          </button>
        </div>

        {/* File Metadata Overview Banner */}
        <div className="border-b border-obsidian-border bg-obsidian-subtle/30 px-4 py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-cockpit-muted">
              <Code2 className="h-3.5 w-3.5 text-cyan-source" />
              <span>{activeFile.lineCount} lines</span>
            </span>
            <span className="text-cockpit-faint">•</span>
            <span className="flex items-center gap-1.5 text-cockpit-muted">
              <Box className="h-3.5 w-3.5 text-amber-warn" />
              <span>{activeFile.functionsCount} functions</span>
            </span>
            <span className="text-cockpit-faint">•</span>
            <span className="flex items-center gap-1.5 text-cockpit-muted">
              <Layers className="h-3.5 w-3.5 text-violet-ai" />
              <span>{activeFile.imports.length} imports</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-[11px] font-mono text-lime-accent bg-lime-accent/10 border border-lime-accent/30 rounded px-2 py-0.5">
              <ShieldCheck className="h-3 w-3" />
              AST Validated
            </span>
          </div>
        </div>

        {/* File Content Preview */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeFile.docstring && (
            <div className="mb-4 rounded-lg border border-obsidian-border bg-obsidian-subtle p-3 text-xs">
              <span className="font-semibold text-cockpit-muted uppercase tracking-wider text-[10px] block mb-1">
                Module Docstring Summary
              </span>
              <p className="text-cockpit-text text-xs leading-relaxed italic">
                "{activeFile.docstring}"
              </p>
            </div>
          )}

          {/* Code Viewer with Syntax and Line Numbers */}
          <CodeBlock
            filename={activeFile.path}
            language="python"
            code={activeFile.content}
          />
        </div>
      </div>
    </div>
  );
};
