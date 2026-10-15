import React, { useState, useMemo } from 'react';
import {
  Network,
  ZoomIn,
  ZoomOut,
  Maximize2,
  ExternalLink,
  Copy,
  Check,
  Search,
  ArrowRight,
  Cpu,
  FileCode,
  Sparkles,
} from 'lucide-react';
import { ARCHITECTURE_DATA } from '../data/projectData';

interface ArchitectureExplorerProps {
  onAskAboutModule: (prompt: string) => void;
}

export const ArchitectureExplorer: React.FC<ArchitectureExplorerProps> = ({
  onAskAboutModule,
}) => {
  const [zoom, setZoom] = useState<number>(1);
  const [selectedModuleId, setSelectedModuleId] = useState<string>('main');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [copiedMermaid, setCopiedMermaid] = useState<boolean>(false);

  const selectedModule = useMemo(() => {
    return (
      ARCHITECTURE_DATA.modules.find((m) => m.id === selectedModuleId) ||
      ARCHITECTURE_DATA.modules[0]
    );
  }, [selectedModuleId]);

  const filteredModules = useMemo(() => {
    if (!searchQuery.trim()) return ARCHITECTURE_DATA.modules;
    const q = searchQuery.toLowerCase();
    return ARCHITECTURE_DATA.modules.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.path.toLowerCase().includes(q) ||
        m.astSymbols.some((s) => s.toLowerCase().includes(q))
    );
  }, [searchQuery]);

  const handleCopyMermaid = async () => {
    try {
      await navigator.clipboard.writeText(ARCHITECTURE_DATA.mermaidCode);
      setCopiedMermaid(true);
      setTimeout(() => setCopiedMermaid(false), 2000);
    } catch (err) {
      console.error('Failed to copy mermaid:', err);
    }
  };

  return (
    <div className="flex flex-1 h-full min-w-0 bg-obsidian-bg overflow-hidden flex-col lg:flex-row">
      {/* Main Canvas Area */}
      <div className="flex flex-1 flex-col h-full min-w-0 overflow-hidden">
        {/* Canvas Toolbar Header */}
        <div className="flex flex-wrap items-center justify-between border-b border-obsidian-border bg-obsidian-subtle/80 px-4 py-2.5 gap-2 shrink-0">
          <div className="flex items-center gap-2">
            <Network className="h-4 w-4 text-violet-ai" />
            <span className="font-semibold text-xs text-cockpit-text">
              Architecture Dependency Canvas
            </span>
            <span className="text-cockpit-faint">•</span>
            <span className="flex items-center gap-1 rounded bg-violet-ai/10 border border-violet-ai/30 px-2 py-0.5 font-mono text-[10px] text-violet-ai">
              <Cpu className="h-3 w-3" />
              AST Deterministic Engine • Zero LLM
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Search Module Filter Input */}
            <div className="relative hidden sm:block">
              <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-cockpit-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter modules..."
                className="w-36 rounded-lg border border-obsidian-border bg-obsidian-bg pl-8 pr-2.5 py-1 text-xs text-cockpit-text placeholder:text-cockpit-faint focus:border-violet-ai/50 focus:outline-none font-mono"
              />
            </div>

            {/* Zoom Controls */}
            <div className="flex items-center rounded-lg border border-obsidian-border bg-obsidian-elevated p-0.5">
              <button
                onClick={() => setZoom((z) => Math.max(0.6, z - 0.1))}
                className="p-1 text-cockpit-muted hover:text-cockpit-text rounded transition-colors"
                title="Zoom out"
              >
                <ZoomOut className="h-3.5 w-3.5" />
              </button>
              <span className="px-2 font-mono text-[10px] text-cockpit-muted select-none">
                {(zoom * 100).toFixed(0)}%
              </span>
              <button
                onClick={() => setZoom((z) => Math.min(1.4, z + 0.1))}
                className="p-1 text-cockpit-muted hover:text-cockpit-text rounded transition-colors"
                title="Zoom in"
              >
                <ZoomIn className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setZoom(1)}
                className="p-1 text-cockpit-muted hover:text-cockpit-text rounded transition-colors border-l border-obsidian-border ml-1 pl-1.5"
                title="Reset zoom"
              >
                <Maximize2 className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Official Draw.io MCP URL Button */}
            <a
              href={ARCHITECTURE_DATA.drawioUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 rounded-lg bg-lime-accent px-3 py-1.5 text-xs font-semibold text-obsidian-bg hover:bg-lime-hover transition-colors shadow-sm cursor-pointer"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              <span>Open in Draw.io</span>
            </a>
          </div>
        </div>

        {/* Visual Graph Canvas Area */}
        <div className="relative flex-1 overflow-auto bg-obsidian-bg cockpit-grid p-6 flex items-center justify-center">
          <div
            style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
            className="relative w-[760px] h-[460px] transition-transform duration-100 select-none"
          >
            {/* SVG Connecting Edges */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="6"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#75D9FF" opacity="0.7" />
                </marker>
                <marker
                  id="arrow-active"
                  viewBox="0 0 10 10"
                  refX="6"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#D2F56A" />
                </marker>
              </defs>

              {/* Edge 1: main -> indexer */}
              <path
                d="M 390 115 L 210 170"
                stroke={selectedModuleId === 'main' || selectedModuleId === 'indexer' ? '#D2F56A' : '#303740'}
                strokeWidth={selectedModuleId === 'main' || selectedModuleId === 'indexer' ? 2 : 1.5}
                strokeDasharray={selectedModuleId === 'main' ? '4 2' : 'none'}
                fill="none"
                markerEnd={selectedModuleId === 'main' || selectedModuleId === 'indexer' ? 'url(#arrow-active)' : 'url(#arrow)'}
              />

              {/* Edge 2: main -> vector_store */}
              <path
                d="M 430 115 L 430 170"
                stroke={selectedModuleId === 'main' || selectedModuleId === 'vector_store' ? '#D2F56A' : '#303740'}
                strokeWidth={selectedModuleId === 'main' || selectedModuleId === 'vector_store' ? 2 : 1.5}
                fill="none"
                markerEnd={selectedModuleId === 'main' || selectedModuleId === 'vector_store' ? 'url(#arrow-active)' : 'url(#arrow)'}
              />

              {/* Edge 3: main -> query_pipeline */}
              <path
                d="M 470 115 L 630 170"
                stroke={selectedModuleId === 'main' || selectedModuleId === 'query_pipeline' ? '#D2F56A' : '#303740'}
                strokeWidth={selectedModuleId === 'main' || selectedModuleId === 'query_pipeline' ? 2 : 1.5}
                fill="none"
                markerEnd={selectedModuleId === 'main' || selectedModuleId === 'query_pipeline' ? 'url(#arrow-active)' : 'url(#arrow)'}
              />

              {/* Edge 4: indexer -> config */}
              <path
                d="M 210 235 L 390 280"
                stroke={selectedModuleId === 'indexer' || selectedModuleId === 'config' ? '#D2F56A' : '#303740'}
                strokeWidth={selectedModuleId === 'indexer' || selectedModuleId === 'config' ? 2 : 1.5}
                fill="none"
                markerEnd={selectedModuleId === 'indexer' || selectedModuleId === 'config' ? 'url(#arrow-active)' : 'url(#arrow)'}
              />

              {/* Edge 5: main -> config */}
              <path
                d="M 370 115 C 320 190, 320 230, 390 280"
                stroke={selectedModuleId === 'main' || selectedModuleId === 'config' ? '#D2F56A' : '#303740'}
                strokeWidth={selectedModuleId === 'main' || selectedModuleId === 'config' ? 2 : 1.5}
                fill="none"
                markerEnd={selectedModuleId === 'main' || selectedModuleId === 'config' ? 'url(#arrow-active)' : 'url(#arrow)'}
              />

              {/* Edge 6: query_pipeline -> config */}
              <path
                d="M 630 235 L 470 280"
                stroke={selectedModuleId === 'query_pipeline' || selectedModuleId === 'config' ? '#D2F56A' : '#303740'}
                strokeWidth={selectedModuleId === 'query_pipeline' || selectedModuleId === 'config' ? 2 : 1.5}
                fill="none"
                markerEnd={selectedModuleId === 'query_pipeline' || selectedModuleId === 'config' ? 'url(#arrow-active)' : 'url(#arrow)'}
              />
            </svg>

            {/* Nodes on Canvas */}
            {filteredModules.map((mod) => {
              const isSelected = mod.id === selectedModuleId;
              return (
                <div
                  key={mod.id}
                  onClick={() => setSelectedModuleId(mod.id)}
                  style={{
                    left: `${mod.x}px`,
                    top: `${mod.y}px`,
                  }}
                  className={`absolute z-10 w-48 rounded-xl border p-3.5 cursor-pointer transition-all shadow-panel ${
                    isSelected
                      ? 'border-lime-accent bg-obsidian-elevated ring-2 ring-lime-accent/30 scale-105'
                      : 'border-obsidian-border bg-obsidian-subtle hover:border-violet-ai/60 hover:bg-obsidian-elevated/70'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-1.5 font-mono text-xs font-semibold text-cockpit-text">
                      <FileCode
                        className={`h-3.5 w-3.5 ${
                          isSelected ? 'text-lime-accent' : 'text-cyan-source'
                        }`}
                      />
                      <span>{mod.name}.py</span>
                    </div>
                    <span className="font-mono text-[10px] text-cockpit-faint">
                      {mod.lineCount}L
                    </span>
                  </div>

                  <p className="text-[11px] text-cockpit-muted line-clamp-1 mb-2">
                    {mod.docstring}
                  </p>

                  <div className="flex items-center justify-between pt-1 border-t border-obsidian-border/60 text-[10px] font-mono text-cockpit-faint">
                    <span>In: {mod.incomingImports.length}</span>
                    <span>Out: {mod.outgoingImports.length}</span>
                    <span>{mod.astSymbols.length} fns</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Canvas Bottom Legend */}
        <div className="flex flex-wrap items-center justify-between border-t border-obsidian-border bg-obsidian-subtle/80 px-4 py-2 text-[11px] font-mono text-cockpit-muted shrink-0">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-lime-accent" />
              <span>Selected Node</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-cyan-source" />
              <span>Import Dependency Edges</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span>Graph ID: target_project_v1</span>
            <span>•</span>
            <button
              onClick={handleCopyMermaid}
              className="text-cyan-source hover:underline flex items-center gap-1 cursor-pointer"
            >
              {copiedMermaid ? <Check className="h-3 w-3 text-lime-accent" /> : <Copy className="h-3 w-3" />}
              <span>{copiedMermaid ? 'Mermaid Copied' : 'Copy Mermaid'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Right Details Inspector (~320px) */}
      <div className="w-full lg:w-80 flex flex-col border-t lg:border-t-0 lg:border-l border-obsidian-border bg-obsidian-subtle/40 shrink-0 overflow-y-auto p-4 space-y-4">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted mb-2">
            Module Inspector
          </div>
          <div className="rounded-xl border border-obsidian-border bg-obsidian-subtle p-3.5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm font-semibold text-lime-accent">
                {selectedModule.name}.py
              </span>
              <span className="rounded bg-obsidian-elevated px-2 py-0.5 font-mono text-[10px] text-cockpit-muted border border-obsidian-border">
                {selectedModule.lineCount} Lines
              </span>
            </div>
            <p className="text-xs text-cockpit-text leading-relaxed">
              {selectedModule.docstring}
            </p>
          </div>
        </div>

        {/* Incoming Imports */}
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
            Incoming Imports ({selectedModule.incomingImports.length})
          </div>
          {selectedModule.incomingImports.length === 0 ? (
            <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle/50 p-2 text-xs text-cockpit-faint">
              Root orchestration module (no incoming imports)
            </div>
          ) : (
            selectedModule.incomingImports.map((caller) => (
              <button
                key={caller}
                onClick={() => setSelectedModuleId(caller)}
                className="flex w-full items-center justify-between rounded-lg border border-obsidian-border bg-obsidian-subtle p-2 text-xs font-mono text-cyan-source hover:bg-obsidian-elevated transition-colors cursor-pointer text-left"
              >
                <span>{caller}.py</span>
                <span className="text-[10px] text-cockpit-faint">imports {selectedModule.name}</span>
              </button>
            ))
          )}
        </div>

        {/* Outgoing Imports */}
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
            Outgoing Dependencies ({selectedModule.outgoingImports.length})
          </div>
          {selectedModule.outgoingImports.length === 0 ? (
            <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle/50 p-2 text-xs text-cockpit-faint">
              Base module (no outgoing project imports)
            </div>
          ) : (
            selectedModule.outgoingImports.map((dep) => (
              <button
                key={dep}
                onClick={() => setSelectedModuleId(dep)}
                className="flex w-full items-center justify-between rounded-lg border border-obsidian-border bg-obsidian-subtle p-2 text-xs font-mono text-violet-ai hover:bg-obsidian-elevated transition-colors cursor-pointer text-left"
              >
                <span>{dep}.py</span>
                <ArrowRight className="h-3 w-3 text-cockpit-faint" />
              </button>
            ))
          )}
        </div>

        {/* Exported AST Symbols */}
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-cockpit-muted">
            Exported AST Symbols
          </div>
          <div className="rounded-lg border border-obsidian-border bg-obsidian-subtle p-2.5 space-y-1 font-mono text-[11px]">
            {selectedModule.astSymbols.map((sym, idx) => (
              <div key={idx} className="text-cockpit-text flex items-center gap-1.5">
                <span className="text-lime-accent">def</span>
                <span>{sym}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Ask Assistant About This Module Action */}
        <div className="pt-2">
          <button
            onClick={() =>
              onAskAboutModule(
                `Inspect imports for target_project/${selectedModule.name}.py and summarize its dependency callers and exports.`
              )
            }
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-obsidian-elevated border border-obsidian-border p-2.5 text-xs font-semibold text-cockpit-text hover:border-lime-accent/50 hover:text-lime-accent transition-colors cursor-pointer"
          >
            <Sparkles className="h-3.5 w-3.5 text-lime-accent" />
            <span>Ask Assistant About {selectedModule.name}.py</span>
          </button>
        </div>
      </div>
    </div>
  );
};
