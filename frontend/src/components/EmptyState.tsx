import React from 'react';
import { Search, FileText, Network, Compass, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt }) => {
  const starterQuestions = [
    {
      agent: 'Code Searcher',
      icon: <Search className="h-4 w-4 text-blue-400" />,
      tag: 'Vector Search (Pinecone)',
      question: 'Where is the chunk_code function implemented?',
      desc: 'Finds exact file locations and line numbers via custom RAG',
    },
    {
      agent: 'Code Explainer',
      icon: <FileText className="h-4 w-4 text-amber-400" />,
      tag: 'Filesystem MCP',
      question: 'What does config.py do?',
      desc: 'Reads complete source files and breaks down logic and variables',
    },
    {
      agent: 'Architecture Mapper',
      icon: <Network className="h-4 w-4 text-purple-400" />,
      tag: 'Python AST',
      question: 'Which files import config.py?',
      desc: 'Deterministic dependency analysis without AI guesses',
    },
    {
      agent: 'Onboarding Guide',
      icon: <Compass className="h-4 w-4 text-emerald-400" />,
      tag: 'Project Setup',
      question: 'How do I get started with this project?',
      desc: 'Entry points, execution commands, and recommended reading order',
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 py-8 max-w-4xl mx-auto text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500/20 to-emerald-700/10 border border-emerald-500/30 text-emerald-400 mb-5 shadow-lg shadow-emerald-950/40">
        <Sparkles className="h-7 w-7" />
      </div>

      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100 mb-2">
        Multi-Agent Code Helper
      </h1>
      <p className="text-slate-400 max-w-lg text-sm sm:text-base mb-8">
        Ask anything about your Python codebase. The Coordinator routes each question to specialized Google ADK agents with custom Pinecone RAG and Filesystem MCP.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full text-left">
        {starterQuestions.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(item.question)}
            className="group flex flex-col p-4 rounded-xl border border-slate-800/90 bg-slate-900/40 hover:bg-slate-900/90 hover:border-emerald-600/50 transition-all duration-200 text-left shadow-sm hover:shadow-md cursor-pointer"
          >
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300">
                {item.icon}
                <span>{item.agent}</span>
              </div>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60">
                {item.tag}
              </span>
            </div>
            <p className="font-medium text-slate-200 text-sm group-hover:text-emerald-300 transition-colors mb-1">
              "{item.question}"
            </p>
            <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
};
