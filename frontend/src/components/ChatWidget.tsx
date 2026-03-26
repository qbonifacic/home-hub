import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, ChevronDown, ChevronUp, Zap } from 'lucide-react';
import { api } from '../api.ts';

interface ChatAction {
  tool: string;
  summary: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  actions?: ChatAction[];
  timestamp: Date;
}

interface Props {
  onActionComplete?: () => void;
}

export default function ChatWidget({ onActionComplete }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/chat', { message: trimmed });
      const data = res.data;

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.response,
        actions: data.actions_taken,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Refresh dashboard if actions were taken
      if (data.actions_taken?.length > 0 && onActionComplete) {
        onActionComplete();
      }
    } catch (err: unknown) {
      let errorMsg = 'Something went wrong. Please try again.';
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 503) {
        errorMsg = 'AI is not configured yet. Set your ANTHROPIC_API_KEY in the .env file and restart the server.';
      } else if (axiosErr.response?.data?.detail) {
        errorMsg = axiosErr.response.data.detail;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: errorMsg,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="bg-bg-card rounded-lg border border-border overflow-hidden">
      {/* Header / Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-bg-hover transition-colors"
      >
        <div className="flex items-center gap-2">
          <MessageSquare className="text-accent" size={18} />
          <h2 className="text-sm font-semibold text-text-primary">Ask Home Hub</h2>
          <span className="text-xs text-text-muted">AI Assistant</span>
        </div>
        {isOpen ? (
          <ChevronUp className="text-text-muted" size={16} />
        ) : (
          <ChevronDown className="text-text-muted" size={16} />
        )}
      </button>

      {/* Chat Body */}
      {isOpen && (
        <div className="border-t border-border">
          {/* Messages Area */}
          <div className="h-72 overflow-y-auto p-3 space-y-3 chat-messages">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <MessageSquare className="text-text-muted mb-2" size={28} />
                <p className="text-sm text-text-muted">
                  Ask me anything about your home!
                </p>
                <div className="mt-3 flex flex-wrap gap-2 justify-center">
                  {[
                    'What chores are overdue?',
                    'Plan keto meals this week',
                    'Kids outdoor time last week?',
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => {
                        setInput(suggestion);
                        inputRef.current?.focus();
                      }}
                      className="text-xs px-3 py-1.5 rounded-full bg-bg-input border border-border text-text-secondary hover:text-text-primary hover:border-accent transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 chat-message-enter ${
                    msg.role === 'user'
                      ? 'bg-accent/20 text-text-primary'
                      : 'bg-bg-input text-text-secondary'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

                  {/* Action badges */}
                  {msg.actions && msg.actions.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {msg.actions.map((action, j) => (
                        <span
                          key={j}
                          className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-status-success/15 text-status-success"
                        >
                          <Zap size={10} />
                          {action.summary}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Thinking indicator */}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-bg-input rounded-lg px-3 py-2">
                  <div className="flex items-center gap-1">
                    <div className="chat-thinking-dot" />
                    <div className="chat-thinking-dot" style={{ animationDelay: '0.2s' }} />
                    <div className="chat-thinking-dot" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-border p-3">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message..."
                disabled={loading}
                className="flex-1 bg-bg-input border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="p-2 rounded-lg bg-accent hover:bg-accent-hover text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
