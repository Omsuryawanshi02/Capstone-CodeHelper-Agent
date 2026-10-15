import React, { useEffect, useRef } from 'react';
import { ChatMessage } from '../types';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { EmptyState } from './EmptyState';

interface ChatMessageListProps {
  messages: ChatMessage[];
  onSelectStarter: (prompt: string) => void;
  onSelectFile?: (filePath: string) => void;
  onNavigateTab?: (tab: 'chat' | 'explorer' | 'architecture' | 'change_review') => void;
}

export const ChatMessageList: React.FC<ChatMessageListProps> = ({
  messages,
  onSelectStarter,
  onSelectFile,
  onNavigateTab,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, messages[messages.length - 1]?.content]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto px-4 sm:px-6">
        <EmptyState onSelectPrompt={onSelectStarter} onNavigateTab={onNavigateTab} />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-4 max-w-4xl mx-auto w-full">
      {messages.map((msg) =>
        msg.role === 'user' ? (
          <UserMessage key={msg.id} message={msg} />
        ) : (
          <AssistantMessage
            key={msg.id}
            message={msg}
            onSelectAction={onSelectStarter}
            onSelectFile={onSelectFile}
          />
        )
      )}
      <div ref={bottomRef} className="h-4" />
    </div>
  );
};
