import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SourceCard } from '../components/SourceCard';
import { AgentActivity } from '../components/AgentActivity';
import { CodeBlock } from '../components/CodeBlock';
import { MarkdownContent } from '../components/MarkdownContent';
import { MessageComposer } from '../components/MessageComposer';
import { EmptyState } from '../components/EmptyState';

describe('SourceCard component', () => {
  it('renders file path, line numbers, and snippet', () => {
    render(
      <SourceCard
        source={{
          filePath: 'target_project/config.py',
          startLine: 10,
          endLine: 25,
          snippet: 'PORT = 8000',
          score: 0.92,
        }}
      />
    );

    expect(screen.getByText('target_project/config.py')).toBeInTheDocument();
    expect(screen.getByText('Lines 10–25')).toBeInTheDocument();
    expect(screen.getByText('PORT = 8000')).toBeInTheDocument();
    expect(screen.getByText('score 92%')).toBeInTheDocument();
  });
});

describe('AgentActivity component', () => {
  it('renders specialist agent label and active operation', () => {
    render(
      <AgentActivity
        agentName="code_searcher"
        activity="Executing vector search in Pinecone..."
      />
    );

    expect(screen.getByText('Code Searcher (RAG)')).toBeInTheDocument();
    expect(screen.getByText('Executing vector search in Pinecone...')).toBeInTheDocument();
  });
});

describe('CodeBlock component', () => {
  it('renders language and code content with copy action', () => {
    render(<CodeBlock language="python" code="def hello(): return 'world'" />);

    expect(screen.getByText('python')).toBeInTheDocument();
    expect(screen.getByText("def hello(): return 'world'")).toBeInTheDocument();
    expect(screen.getByText('Copy')).toBeInTheDocument();
  });
});

describe('MarkdownContent component', () => {
  it('renders headers, bold, and inline code properly', () => {
    const markdown = '## Architecture\nUse **Pinecone** for `vector_store.py`';
    render(<MarkdownContent content={markdown} />);

    expect(screen.getByText('Architecture')).toBeInTheDocument();
    expect(screen.getByText('Pinecone')).toBeInTheDocument();
    expect(screen.getByText('vector_store.py')).toBeInTheDocument();
  });
});

describe('MessageComposer component', () => {
  it('prevents submission when input is whitespace only', () => {
    const handleSend = vi.fn();
    render(
      <MessageComposer
        onSend={handleSend}
        onCancel={vi.fn()}
        isStreaming={false}
      />
    );

    const textarea = screen.getByPlaceholderText(/ask where code is/i);
    fireEvent.change(textarea, { target: { value: '   ' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    expect(handleSend).not.toHaveBeenCalled();
  });

  it('submits on Enter key without shift', () => {
    const handleSend = vi.fn();
    render(
      <MessageComposer
        onSend={handleSend}
        onCancel={vi.fn()}
        isStreaming={false}
      />
    );

    const textarea = screen.getByPlaceholderText(/ask where code is/i);
    fireEvent.change(textarea, { target: { value: 'Where is Pinecone initialized?' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    expect(handleSend).toHaveBeenCalledWith('Where is Pinecone initialized?');
  });

  it('allows newline on Shift+Enter', () => {
    const handleSend = vi.fn();
    render(
      <MessageComposer
        onSend={handleSend}
        onCancel={vi.fn()}
        isStreaming={false}
      />
    );

    const textarea = screen.getByPlaceholderText(/ask where code is/i);
    fireEvent.change(textarea, { target: { value: 'Line 1' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });

    expect(handleSend).not.toHaveBeenCalled();
  });
});

describe('EmptyState component', () => {
  it('renders all four starter questions and triggers callback on click', () => {
    const handleSelect = vi.fn();
    render(<EmptyState onSelectPrompt={handleSelect} />);

    expect(screen.getByText(/where is the chunk_code function implemented/i)).toBeInTheDocument();
    expect(screen.getByText(/what does config\.py do/i)).toBeInTheDocument();
    expect(screen.getByText(/which files import config\.py/i)).toBeInTheDocument();
    expect(screen.getByText(/how do i get started with this project/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText(/what does config\.py do/i));
    expect(handleSelect).toHaveBeenCalledWith('What does config.py do?');
  });
});
