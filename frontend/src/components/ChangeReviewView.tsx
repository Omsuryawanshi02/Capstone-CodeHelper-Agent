import React, { useState } from 'react';
import {
  GitBranch,
  AlertTriangle,
  Copy,
  Check,
  FileCode,
  ArrowRight,
  Terminal,
  Sparkles,
} from 'lucide-react';
import { CHANGE_REVIEW_DATA } from '../data/projectData';
import { ChangedFile } from '../types';

interface ChangeReviewViewProps {
  onAskAboutChanges: (prompt: string) => void;
}

export const ChangeReviewView: React.FC<ChangeReviewViewProps> = ({
  onAskAboutChanges,
}) => {
  const [selectedFilePath, setSelectedFilePath] = useState<string>(
    CHANGE_REVIEW_DATA.changedFiles[0].path
  );
  const [copiedTest, setCopiedTest] = useState<string | null>(null);

  const activeFile: ChangedFile =
    CHANGE_REVIEW_DATA.changedFiles.find((f) => f.path === selectedFilePath) ||
    CHANGE_REVIEW_DATA.changedFiles[0];

  const handleCopyCommand = async (cmd: string) => {
    try {
      await navigator.clipboard.writeText(cmd);
      setCopiedTest(cmd);
      setTimeout(() => setCopiedTest(null), 2000);
    } catch (err) {
      console.error('Failed to copy test command:', err);
    }
  };

  return (
    <div className="flex flex-1 h-full min-w-0 bg-obsidian-bg overflow-hidden flex-col md:flex-row">
      {/* Left Sidebar: Changed Files & Risk Summary (~280px) */}
      <div className="flex w-full md:w-80 flex-col border-b md:border-b-0 md:border-r border-obsidian-border bg-obsidian-subtle/50 shrink-0">
        {/* Git Header */}
        <div className="p-3.5 border-b border-obsidian-border bg-obsidian-subtle/80 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 font-mono text-xs text-cockpit-text font-semibold">
              <GitBranch className="h-4 w-4 text-lime-accent" />
              <span>{CHANGE_REVIEW_DATA.branch}</span>
            </div>
            <span className="font-mono text-[10px] text-cockpit-faint">
              {CHANGE_REVIEW_DATA.baseCommit}...{CHANGE_REVIEW_DATA.targetCommit}
            </span>
          </div>

          {/* Risk Label with Evidence-Based Explanation */}
          <div className="rounded-lg border border-amber-warn/40 bg-amber-warn/5 p-2.5 text-xs text-amber-warn space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold uppercase tracking-wider text-[11px] flex items-center gap-1">
                <AlertTriangle className="h-3.5 w-3.5" />
                {CHANGE_REVIEW_DATA.riskLevel} Risk
              </span>
              <span className="rounded bg-amber-warn/10 border border-amber-warn/30 px-1.5 py-0.2 font-mono text-[10px]">
                [{CHANGE_REVIEW_DATA.confidence}]
              </span>
            </div>
            <p className="text-[11px] text-cockpit-muted leading-relaxed">
              {CHANGE_REVIEW_DATA.riskExplanation}
            </p>
          </div>
        </div>

        {/* Changed Files List Header */}
        <div className="flex items-center justify-between px-3.5 py-2 text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted border-b border-obsidian-border/50">
          <span>Changed Files ({CHANGE_REVIEW_DATA.changedFiles.length})</span>
          <span className="font-mono text-[10px] text-lime-accent">
            +44 / -3 lines
          </span>
        </div>

        {/* Changed Files List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {CHANGE_REVIEW_DATA.changedFiles.map((file) => {
            const isSelected = file.path === activeFile.path;
            return (
              <button
                key={file.path}
                onClick={() => setSelectedFilePath(file.path)}
                className={`flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-2.5 text-left text-xs transition-colors cursor-pointer ${
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
                  <div className="truncate">
                    <span className="font-mono block truncate">{file.path}</span>
                    <span className="text-[10px] font-sans text-cockpit-faint capitalize">
                      {file.status} {file.isStaged ? '• staged' : '• unstaged'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 font-mono text-[10px] shrink-0">
                  <span className="text-lime-accent">+{file.additions}</span>
                  <span className="text-red-err">-{file.deletions}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Ask Assistant about changes */}
        <div className="p-3 border-t border-obsidian-border bg-obsidian-bg">
          <button
            onClick={() =>
              onAskAboutChanges(
                'Perform a 10-step code change analysis on target_project working tree diff with AST verification, downstream callers, and test suggestions.'
              )
            }
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-lime-accent p-2.5 text-xs font-semibold text-obsidian-bg hover:bg-lime-hover transition-colors shadow-sm cursor-pointer"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Generate Full Change Report</span>
          </button>
        </div>
      </div>

      {/* Main Diff & AST Inspector Area */}
      <div className="flex flex-1 flex-col h-full min-w-0 overflow-hidden bg-obsidian-bg">
        {/* File Header Bar */}
        <div className="flex flex-wrap items-center justify-between border-b border-obsidian-border bg-obsidian-subtle/80 px-4 py-2.5 gap-2 shrink-0">
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-cockpit-muted">Diff:</span>
            <span className="text-cockpit-text font-semibold">{activeFile.path}</span>
            <span
              className={`rounded px-1.5 py-0.2 font-mono text-[10px] uppercase border ${
                activeFile.status === 'modified'
                  ? 'border-amber-warn/40 bg-amber-warn/10 text-amber-warn'
                  : 'border-lime-accent/40 bg-lime-accent/10 text-lime-accent'
              }`}
            >
              {activeFile.status}
            </span>
            {activeFile.isStaged && (
              <span className="rounded bg-obsidian-elevated px-1.5 py-0.2 text-[10px] text-cockpit-muted border border-obsidian-border">
                Staged
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-lime-accent font-semibold">+{activeFile.additions}</span>
            <span className="text-red-err font-semibold">-{activeFile.deletions}</span>
          </div>
        </div>

        {/* AST Structural Changes & Downstream Impact Summary */}
        <div className="border-b border-obsidian-border bg-obsidian-subtle/30 p-4 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs shrink-0">
          {/* AST Modifications */}
          <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle p-3 space-y-1.5">
            <span className="font-semibold text-cockpit-muted uppercase tracking-wider text-[10px] block">
              AST Structural Modifications [Confirmed]
            </span>
            <div className="font-mono text-[11px] space-y-1">
              {activeFile.astDifferences.addedFunctions.length > 0 && (
                <div className="text-lime-accent">
                  + Added function:{' '}
                  <span className="text-cockpit-text font-semibold">
                    {activeFile.astDifferences.addedFunctions.join(', ')}
                  </span>
                </div>
              )}
              {activeFile.astDifferences.modifiedFunctions.length > 0 && (
                <div className="text-amber-warn">
                  ~ Modified signature:{' '}
                  <span className="text-cockpit-text font-semibold">
                    {activeFile.astDifferences.modifiedFunctions.join(', ')}
                  </span>
                </div>
              )}
              {activeFile.astDifferences.addedClasses.length > 0 && (
                <div className="text-lime-accent">
                  + Added class:{' '}
                  <span className="text-cockpit-text font-semibold">
                    {activeFile.astDifferences.addedClasses.join(', ')}
                  </span>
                </div>
              )}
              {activeFile.astDifferences.addedFunctions.length === 0 &&
                activeFile.astDifferences.modifiedFunctions.length === 0 &&
                activeFile.astDifferences.addedClasses.length === 0 && (
                  <div className="text-cockpit-faint">No top-level signature changes detected.</div>
                )}
            </div>
          </div>

          {/* Downstream Callers Impact */}
          <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle p-3 space-y-1.5">
            <span className="font-semibold text-cockpit-muted uppercase tracking-wider text-[10px] block">
              Downstream Dependent Modules [Likely]
            </span>
            <div className="font-mono text-[11px] space-y-1 text-cockpit-muted">
              {CHANGE_REVIEW_DATA.downstreamImpacts
                .find((d) => d.sourceFile === activeFile.path)
                ?.affectedCallers.map((caller, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-cyan-source">
                    <ArrowRight className="h-3 w-3 text-cockpit-faint" />
                    <span>{caller}</span>
                  </div>
                )) || (
                <div className="text-cockpit-faint">
                  No direct callers found in target_project import graph.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Diff Viewer */}
        <div className="flex-1 overflow-y-auto p-4 font-mono text-xs">
          <div className="rounded-xl border border-obsidian-border bg-obsidian-bg overflow-hidden shadow-panel">
            <table className="w-full border-collapse">
              <tbody>
                {activeFile.diffLines.map((line, idx) => {
                  const isAdd = line.type === 'add';
                  const isDelete = line.type === 'delete';
                  return (
                    <tr
                      key={idx}
                      className={
                        isAdd
                          ? 'bg-lime-accent/10 text-lime-accent hover:bg-lime-accent/15'
                          : isDelete
                          ? 'bg-red-err/10 text-red-err hover:bg-red-err/15'
                          : 'hover:bg-obsidian-elevated/40 text-cockpit-muted'
                      }
                    >
                      <td className="w-10 pr-2 pl-3 py-0.5 text-right text-[11px] select-none text-cockpit-faint border-r border-obsidian-border/50">
                        {line.oldLineNumber || ''}
                      </td>
                      <td className="w-10 pr-2 pl-2 py-0.5 text-right text-[11px] select-none text-cockpit-faint border-r border-obsidian-border/50">
                        {line.newLineNumber || ''}
                      </td>
                      <td className="px-3 py-0.5 whitespace-pre leading-relaxed font-mono">
                        {line.text}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Recommended Tests Section */}
          <div className="mt-5 space-y-2">
            <span className="font-semibold text-cockpit-muted uppercase tracking-wider text-[11px] block">
              Recommended Validation Commands [Likely]
            </span>
            <div className="space-y-1.5">
              {CHANGE_REVIEW_DATA.recommendedTests.map((cmd, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between rounded-lg border border-obsidian-border bg-obsidian-subtle px-3 py-2 text-xs font-mono"
                >
                  <div className="flex items-center gap-2 truncate text-cockpit-text">
                    <Terminal className="h-3.5 w-3.5 text-lime-accent shrink-0" />
                    <span className="truncate">{cmd}</span>
                  </div>
                  <button
                    onClick={() => handleCopyCommand(cmd)}
                    className="p-1 text-cockpit-muted hover:text-cockpit-text rounded transition-colors cursor-pointer"
                    title="Copy command"
                  >
                    {copiedTest === cmd ? (
                      <Check className="h-3.5 w-3.5 text-lime-accent" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
