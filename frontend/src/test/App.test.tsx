import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { App } from '../App';
import * as healthApi from '../api/health';
import * as sessionsApi from '../api/sessions';
import * as chatApi from '../api/chat';

vi.mock('../api/health');
vi.mock('../api/sessions');
vi.mock('../api/chat');

describe('App component integration', () => {
  beforeEach(() => {
    vi.resetAllMocks();

    vi.mocked(healthApi.fetchHealth).mockResolvedValue({
      status: 'ok',
      backendRunning: true,
      adkReachable: true,
      adkAppName: 'code_helper',
      configValid: true,
    });

    vi.mocked(sessionsApi.listSessions).mockResolvedValue([
      {
        sessionId: 'session-101',
        title: 'Initial Session',
        createdAt: 1000,
        messageCount: 1,
      },
    ]);

    vi.mocked(sessionsApi.createSession).mockImplementation(async (title) => ({
      sessionId: 'session-new',
      title: title || 'New Conversation',
      createdAt: 2000,
      messageCount: 0,
    }));
  });

  it('renders initial state and connected health badge', async () => {
    render(<App />);

    expect(screen.getAllByText('Code Helper AI').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('target_project').length).toBeGreaterThanOrEqual(1);

    await waitFor(() => {
      expect(screen.getByText('Services Connected')).toBeInTheDocument();
      expect(screen.getByText('Initial Session')).toBeInTheDocument();
    });
  });

  it('submits a message and handles streamed events in-place', async () => {
    vi.mocked(chatApi.streamChatMessage).mockImplementation(async (sessionId, _message, onEvent) => {
      await Promise.resolve();
      onEvent({
        type: 'agent_activity',
        session_id: sessionId,
        agent_name: 'code_searcher',
        activity: 'Searching indexed code in Pinecone...',
      });
      await Promise.resolve();
      onEvent({
        type: 'token',
        session_id: sessionId,
        text: 'The chunk_code function is located in ',
      });
      await Promise.resolve();
      onEvent({
        type: 'token',
        session_id: sessionId,
        text: 'target_project/indexer.py at lines 44-108.',
      });
      await Promise.resolve();
      onEvent({
        type: 'source',
        session_id: sessionId,
        file_path: 'target_project/indexer.py',
        start_line: 44,
        end_line: 108,
        score: 0.95,
      });
      await Promise.resolve();
      onEvent({
        type: 'done',
        session_id: sessionId,
      });
    });

    render(<App />);
    await screen.findByText('Initial Session');

    // Click starter question
    const questionButton = await screen.findByText(/where is the chunk_code function implemented/i);
    fireEvent.click(questionButton);

    // Verify user message appears
    expect(
      await screen.findByText('Where is the chunk_code function implemented?')
    ).toBeInTheDocument();

    // Verify streamed response appears
    expect(
      await screen.findByText(/The chunk_code function is located in target_project\/indexer\.py at lines 44-108\./i)
    ).toBeInTheDocument();

    // Verify grounded source card appears
    expect(await screen.findByText('Lines 44–108')).toBeInTheDocument();
    expect(screen.getByText('score 95%')).toBeInTheDocument();
  });

  it('handles and displays error events safely', async () => {
    vi.mocked(chatApi.streamChatMessage).mockImplementation(async (sessionId, _message, onEvent) => {
      await Promise.resolve();
      onEvent({
        type: 'error',
        session_id: sessionId,
        error: 'Target project file not found',
      });
      await Promise.resolve();
      onEvent({
        type: 'done',
        session_id: sessionId,
      });
    });

    render(<App />);
    await screen.findByText('Initial Session');

    const questionButton = await screen.findByText(/what does config\.py do/i);
    fireEvent.click(questionButton);

    const matches = await screen.findAllByText(/Target project file not found/i);
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it('creates new conversation session when clicking New Conversation', async () => {
    render(<App />);

    const newChatButton = await screen.findByText('New Conversation');
    fireEvent.click(newChatButton);

    await waitFor(() => {
      expect(sessionsApi.createSession).toHaveBeenCalled();
    });
  });
});
