import { API_BASE_URL, ApiError } from './client';
import { SessionItem } from '../types';

export async function createSession(title?: string): Promise<SessionItem> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new ApiError(`Failed to create session: ${response.statusText}`, response.status, errorBody);
  }

  const data = await response.json();
  return {
    sessionId: data.session_id,
    title: data.title || title || 'New Conversation',
    createdAt: data.created_at,
    lastMessageAt: data.created_at,
    messageCount: 0,
  };
}

export async function listSessions(): Promise<SessionItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new ApiError(`Failed to list sessions: ${response.statusText}`, response.status);
  }

  const items = await response.json();
  return items.map((item: any) => ({
    sessionId: item.session_id,
    title: item.title || 'Conversation',
    createdAt: item.created_at,
    lastMessageAt: item.last_message_at,
    messageCount: item.message_count || 0,
  }));
}
