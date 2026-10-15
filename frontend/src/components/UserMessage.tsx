import React from 'react';
import { User } from 'lucide-react';
import { ChatMessage } from '../types';

interface UserMessageProps {
  message: ChatMessage;
}

export const UserMessage: React.FC<UserMessageProps> = ({ message }) => {
  return (
    <div className="flex w-full justify-end py-2">
      <div className="flex max-w-[85%] items-start gap-2.5 flex-row-reverse">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-obsidian-elevated text-lime-accent border border-obsidian-border shadow-sm mt-0.5">
          <User className="h-3.5 w-3.5" />
        </div>

        <div className="space-y-1 text-right">
          <div className="inline-block rounded-xl rounded-tr-none border border-obsidian-border bg-obsidian-elevated px-4 py-2.5 text-xs text-cockpit-text shadow-sm leading-relaxed text-left">
            {message.content}
          </div>
          <div className="text-[10px] text-cockpit-faint px-1">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    </div>
  );
};
