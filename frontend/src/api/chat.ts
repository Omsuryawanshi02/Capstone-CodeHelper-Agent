import { API_BASE_URL, ApiError } from './client';
import { NormalizedSSEEvent } from '../types';

export async function streamChatMessage(
  sessionId: string,
  message: string,
  onEvent: (event: NormalizedSSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
    }),
    signal,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new ApiError(`Chat request failed with status ${response.status}`, response.status, errorBody);
  }

  if (!response.body) {
    throw new ApiError('Response body is null, cannot stream events.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      // Keep last incomplete segment in buffer
      buffer = lines.pop() || '';

      for (const block of lines) {
        const trimmed = block.trim();
        if (!trimmed) continue;

        // An SSE data block can contain multiple data: lines
        const dataLines = trimmed
          .split('\n')
          .filter((line) => line.startsWith('data: '))
          .map((line) => line.slice(6).trim());

        for (const dataStr of dataLines) {
          if (!dataStr) continue;
          try {
            const event: NormalizedSSEEvent = JSON.parse(dataStr);
            onEvent(event);
          } catch (err) {
            console.warn('Failed to parse SSE event chunk:', dataStr, err);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
