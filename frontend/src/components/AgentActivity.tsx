import React from 'react';
import { Search, FileText, Network, Compass, Bot, Loader2 } from 'lucide-react';

interface AgentActivityProps {
  agentName?: string;
  activity?: string;
}

export const AgentActivity: React.FC<AgentActivityProps> = ({ agentName, activity }) => {
  const getAgentIcon = (name?: string) => {
    switch (name) {
      case 'code_searcher':
        return <Search className="h-3.5 w-3.5 text-blue-400" />;
      case 'code_explainer':
        return <FileText className="h-3.5 w-3.5 text-amber-400" />;
      case 'architecture_mapper':
        return <Network className="h-3.5 w-3.5 text-purple-400" />;
      case 'onboarding_guide':
        return <Compass className="h-3.5 w-3.5 text-emerald-400" />;
      default:
        return <Bot className="h-3.5 w-3.5 text-emerald-400" />;
    }
  };

  const getAgentLabel = (name?: string) => {
    switch (name) {
      case 'code_searcher':
        return 'Code Searcher (RAG)';
      case 'code_explainer':
        return 'Code Explainer (MCP)';
      case 'architecture_mapper':
        return 'Architecture Mapper (AST)';
      case 'onboarding_guide':
        return 'Onboarding Guide';
      case 'coordinator':
        return 'Coordinator';
      default:
        return name || 'Specialist Agent';
    }
  };

  return (
    <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/80 px-3 py-1 text-xs text-slate-300 shadow-sm w-fit animate-pulse">
      <Loader2 className="h-3 w-3 animate-spin text-emerald-400" />
      <div className="flex items-center gap-1.5 font-medium">
        {getAgentIcon(agentName)}
        <span className="text-slate-200">{getAgentLabel(agentName)}</span>
      </div>
      {activity && (
        <>
          <span className="text-slate-600">•</span>
          <span className="text-slate-400 font-normal truncate max-w-xs">{activity}</span>
        </>
      )}
    </div>
  );
};
