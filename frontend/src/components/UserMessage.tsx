import React from 'react';
import { User } from 'lucide-react';
import { ChatMessage } from '../types';

interface UserMessageProps {
  message: ChatMessage;
}

export const UserMessage: React.FC<UserMessageProps> = ({ message }) => {
  return (
    <div className="flex w-full justify-end py-2">
      <div className="flex max-w-[85%] sm:max-w-[75%] items-start gap-3">
        <div className="rounded-2xl rounded-tr-none bg-emerald-600 px-4 py-3 text-white shadow-sm text-sm sm:text-base leading-relaxed break-words">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-800/80 text-emerald-200 border border-emerald-600/40">
          <User className="h-4 w-4" />
        </div>
      </div>
    </div>
  );
};
