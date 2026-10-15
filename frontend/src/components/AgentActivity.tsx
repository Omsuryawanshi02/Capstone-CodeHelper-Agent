import React from 'react';
import { Search, FileText, Network, Compass, Bot, Loader2, CheckCircle2 } from 'lucide-react';
import { AgentName } from '../types';

interface AgentActivityProps {
  agentName?: AgentName | string;
  activity?: string;
  isComplete?: boolean;
}

export const AgentActivity: React.FC<AgentActivityProps> = ({
  agentName,
  activity,
  isComplete = false,
}) => {
  const getAgentConfig = (name?: string) => {
    switch (name) {
      case 'code_searcher':
        return {
          icon: <Search className="h-3 w-3 text-cyan-source" />,
          label: 'Code Searcher (RAG)',
          subtext: 'Pinecone RAG + NVIDIA NIM',
          badgeColor: 'border-cyan-source/40 bg-cyan-source/10 text-cyan-source',
        };
      case 'code_explainer':
        return {
          icon: <FileText className="h-3 w-3 text-amber-warn" />,
          label: 'Code Explainer',
          subtext: 'Filesystem MCP',
          badgeColor: 'border-amber-warn/40 bg-amber-warn/10 text-amber-warn',
        };
      case 'architecture_mapper':
        return {
          icon: <Network className="h-3 w-3 text-violet-ai" />,
          label: 'Architecture Mapper',
          subtext: 'Deterministic AST Analysis • Zero LLM',
          badgeColor: 'border-violet-ai/40 bg-violet-ai/10 text-violet-ai',
        };
      case 'onboarding_guide':
        return {
          icon: <Compass className="h-3 w-3 text-lime-accent" />,
          label: 'Onboarding Guide',
          subtext: 'Repository Structure',
          badgeColor: 'border-lime-accent/40 bg-lime-accent/10 text-lime-accent',
        };
      case 'coordinator':
        return {
          icon: <Bot className="h-3 w-3 text-lime-accent" />,
          label: 'Coordinator Agent',
          subtext: 'Google ADK Root Router',
          badgeColor: 'border-lime-accent/40 bg-lime-accent/10 text-lime-accent',
        };
      default:
        return {
          icon: <Bot className="h-3 w-3 text-violet-ai" />,
          label: name || 'Specialist Agent',
          subtext: 'Google ADK Agent',
          badgeColor: 'border-violet-ai/40 bg-violet-ai/10 text-violet-ai',
        };
    }
  };

  const config = getAgentConfig(agentName);

  return (
    <div className="flex items-center gap-2 rounded-full border border-obsidian-border bg-obsidian-subtle px-3 py-1 text-xs text-cockpit-muted shadow-sm w-fit max-w-full">
      {isComplete ? (
        <CheckCircle2 className="h-3.5 w-3.5 text-lime-accent shrink-0" />
      ) : (
        <Loader2 className="h-3.5 w-3.5 animate-spin text-lime-accent shrink-0" />
      )}

      <div className="flex items-center gap-1.5 font-medium shrink-0">
        {config.icon}
        <span className="text-cockpit-text">{config.label}</span>
      </div>

      <span className="hidden sm:inline rounded px-1.5 py-0.2 font-mono text-[10px] border border-obsidian-border bg-obsidian-elevated text-cockpit-muted">
        {config.subtext}
      </span>

      {activity && (
        <>
          <span className="text-cockpit-faint">•</span>
          <span className="text-cockpit-muted font-normal truncate max-w-sm" title={activity}>
            {activity}
          </span>
        </>
      )}
    </div>
  );
};
