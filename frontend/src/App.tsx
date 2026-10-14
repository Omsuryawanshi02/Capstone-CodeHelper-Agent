import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatHeader } from './components/ChatHeader';
import { ChatMessageList } from './components/ChatMessageList';
import { MessageComposer } from './components/MessageComposer';
import { ChatMessage, SessionItem, HealthState, SourceItem, NormalizedSSEEvent } from './types';
import { fetchHealth } from './api/health';
import { createSession, listSessions } from './api/sessions';
import { streamChatMessage } from './api/chat';

export const App: React.FC = () => {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messagesBySession, setMessagesBySession] = useState<Record<string, ChatMessage[]>>({});
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthState>({
    status: 'checking',
    backendRunning: false,
    adkReachable: false,
    adkAppName: 'code_helper',
    configValid: false,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  // Poll backend health on mount and every 20 seconds
  useEffect(() => {
    const checkStatus = async () => {
      const state = await fetchHealth();
      setHealth(state);
    };

    checkStatus();
    const interval = setInterval(checkStatus, 20000);
    return () => clearInterval(interval);
  }, []);

  // Load recent sessions on mount
  useEffect(() => {
    let mounted = true;
    const initSessions = async () => {
      try {
        const remoteSessions = await listSessions();
        if (mounted) {
          setSessions(remoteSessions);
          setActiveSessionId((current) => {
            if (current) return current;
            return remoteSessions.length > 0 ? remoteSessions[0].sessionId : null;
          });
        }
      } catch (err) {
        console.debug('Could not load existing sessions on initial load:', err);
      }
    };
    initSessions();
    return () => {
      mounted = false;
    };
  }, []);

  const activeMessages = activeSessionId ? messagesBySession[activeSessionId] || [] : [];

  const handleNewChat = async () => {
    try {
      const newSession = await createSession('New Conversation');
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.sessionId);
      setMessagesBySession((prev) => ({ ...prev, [newSession.sessionId]: [] }));
      setError(null);
    } catch (err: any) {
      // Fallback local session ID if backend is starting up
      const localId = `local-${Date.now()}`;
      const fallbackSession: SessionItem = {
        sessionId: localId,
        title: 'New Conversation',
        createdAt: Date.now() / 1000,
        messageCount: 0,
      };
      setSessions((prev) => [fallbackSession, ...prev]);
      setActiveSessionId(localId);
      setMessagesBySession((prev) => ({ ...prev, [localId]: [] }));
    }
  };

  const handleSelectSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
    setError(null);
  };

  const handleCancelStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);

    if (activeSessionId) {
      setMessagesBySession((prev) => {
        const currentMsgs = prev[activeSessionId] || [];
        return {
          ...prev,
          [activeSessionId]: currentMsgs.map((m, i) =>
            i === currentMsgs.length - 1 && m.isStreaming ? { ...m, isStreaming: false } : m
          ),
        };
      });
    }
  };

  const handleSendMessage = async (text: string) => {
    if (isStreaming) return;
    setError(null);

    // Resolve or create session
    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      try {
        const newSession = await createSession(text.slice(0, 30));
        setSessions((prev) => [newSession, ...prev]);
        targetSessionId = newSession.sessionId;
        setActiveSessionId(targetSessionId);
      } catch {
        targetSessionId = `session-${Date.now()}`;
        setActiveSessionId(targetSessionId);
      }
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };

    const assistantMsgId = `assistant-${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
      sources: [],
    };

    // Update conversation state
    setMessagesBySession((prev) => {
      const existing = prev[targetSessionId!] || [];
      return {
        ...prev,
        [targetSessionId!]: [...existing, userMessage, initialAssistantMsg],
      };
    });

    setIsStreaming(true);
    abortControllerRef.current = new AbortController();

    try {
      await streamChatMessage(
        targetSessionId!,
        text,
        (event: NormalizedSSEEvent) => {
          setMessagesBySession((prev) => {
            const currentList = prev[targetSessionId!] || [];
            const updated = currentList.map((msg) => {
              if (msg.id !== assistantMsgId) return msg;

              switch (event.type) {
                case 'status':
                  return {
                    ...msg,
                    activity: event.text || msg.activity,
                  };
                case 'agent_activity':
                  return {
                    ...msg,
                    agentName: event.agent_name || msg.agentName,
                    activity: event.activity || msg.activity,
                  };
                case 'token':
                  return {
                    ...msg,
                    content: msg.content + (event.text || ''),
                    agentName: event.agent_name || msg.agentName,
                  };
                case 'message':
                  return {
                    ...msg,
                    content: event.text || msg.content,
                    agentName: event.agent_name || msg.agentName,
                  };
                case 'source':
                  if (!event.file_path) return msg;
                  const newSource: SourceItem = {
                    filePath: event.file_path,
                    startLine: event.start_line,
                    endLine: event.end_line,
                    snippet: event.snippet,
                    score: event.score,
                  };
                  const currentSources = msg.sources || [];
                  // Deduplicate sources
                  const exists = currentSources.some(
                    (s) =>
                      s.filePath === newSource.filePath &&
                      s.startLine === newSource.startLine &&
                      s.endLine === newSource.endLine
                  );
                  return exists ? msg : { ...msg, sources: [...currentSources, newSource] };
                case 'error':
                  setError(event.error || 'Agent returned an error');
                  return {
                    ...msg,
                    isStreaming: false,
                    content: msg.content || (event.error ? `Error: ${event.error}` : 'An error occurred.'),
                  };
                case 'done':
                  return {
                    ...msg,
                    isStreaming: false,
                  };
                default:
                  return msg;
              }
            });
            return { ...prev, [targetSessionId!]: updated };
          });
        },
        abortControllerRef.current.signal
      );
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        const errorMsg = err.message || 'Failed to stream response from backend';
        setError(errorMsg);
        setMessagesBySession((prev) => {
          const currentList = prev[targetSessionId!] || [];
          return {
            ...prev,
            [targetSessionId!]: currentList.map((m) =>
              m.id === assistantMsgId
                ? {
                    ...m,
                    isStreaming: false,
                    content: m.content || `Connection error: ${errorMsg}. Verify backend is running on :8001.`,
                  }
                : m
            ),
          };
        });
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex h-full w-full overflow-hidden bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        health={health}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main chat column */}
      <main className="flex flex-1 flex-col h-full min-w-0 bg-slate-950">
        <ChatHeader
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
          activeSessionId={activeSessionId}
          health={health}
        />

        <ChatMessageList
          messages={activeMessages}
          onSelectStarter={handleSendMessage}
        />

        <MessageComposer
          onSend={handleSendMessage}
          onCancel={handleCancelStream}
          isStreaming={isStreaming}
          disabled={isStreaming}
          error={error}
          onClearError={() => setError(null)}
        />
      </main>
    </div>
  );
};

export default App;
