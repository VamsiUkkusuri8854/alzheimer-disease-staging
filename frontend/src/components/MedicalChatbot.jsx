// ============================================================
// NEUROSTAGE AI — MEDICAL ASSISTANT CHATBOT COMPONENT
// ============================================================

import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  User,
  ShieldAlert,
  ExternalLink,
  RotateCcw,
  Minus,
  HelpCircle,
  BrainCircuit,
  AlertTriangle
} from 'lucide-react';
import { sendChatMessage } from '../services/api';

const STARTER_QUESTIONS = [
  "What does my MRI result mean?",
  "What are the early signs of Alzheimer’s?",
  "How can I reduce Alzheimer's risk?",
  "What is CDR 0.5?",
  "When should I see a doctor?"
];

export default function MedicalChatbot({
  isOpen,
  onToggle,
  mriContext,
  initialMessage = null,
  onClearInitialMessage = null
}) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: (
        "Hello! I'm your Alzheimer's medical information assistant. I can help you understand Alzheimer's disease, " +
        "MRI results, risk factors, prevention, and more. How can I help you?"
      ),
      sources: [],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, messages]);

  // Handle triggered initial message (e.g. from "Ask AI Assistant About This Result")
  useEffect(() => {
    if (initialMessage && isOpen) {
      handleSend(initialMessage);
      if (onClearInitialMessage) {
        onClearInitialMessage();
      }
    }
  }, [initialMessage, isOpen]);

  const handleSend = async (messageToSend = null) => {
    const text = (messageToSend !== null ? messageToSend : inputValue).trim();
    if (!text || loading) return;

    setErrorMsg(null);
    setInputValue('');

    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setLoading(true);

    try {
      // Prepare previous turns for conversation context
      const historyContext = newHistory
        .filter((m) => m.id !== 'welcome')
        .slice(-6)
        .map((m) => ({
          sender: m.sender,
          text: m.text
        }));

      const res = await sendChatMessage(text, historyContext, mriContext);

      const botMsg = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: res.answer,
        sources: res.sources || [],
        category: res.category,
        disclaimer: res.disclaimer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      const fallbackMsg = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: "I'm unable to connect to the medical assistant service right now. Please try again in a moment.",
        isError: true,
        sources: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        text: (
          "Chat history cleared.\n\n" +
          "How can I help you today with Alzheimer's information or your MRI analysis?"
        ),
        sources: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setErrorMsg(null);
  };

  // Helper to render markdown bold and line breaks safely
  const formatMessageText = (rawText) => {
    if (!rawText) return null;
    return rawText.split('\n\n').map((paragraph, pIdx) => {
      const lines = paragraph.split('\n').map((line, lIdx) => {
        // Parse bold **text**
        const parts = line.split(/(\*\*.*?\*\*)/g);
        return (
          <span key={lIdx} style={{ display: 'block', marginBottom: lIdx < paragraph.split('\n').length - 1 ? '4px' : '0' }}>
            {parts.map((part, idx) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={idx} style={{ color: '#0f172a' }}>{part.slice(2, -2)}</strong>;
              }
              return part;
            })}
          </span>
        );
      });
      return (
        <div key={pIdx} style={{ marginBottom: pIdx < rawText.split('\n\n').length - 1 ? '10px' : '0' }}>
          {lines}
        </div>
      );
    });
  };

  return (
    <>
      {/* 1. FLOATING ACTION BUTTON (BOTTOM-RIGHT WITH BADGE 1) */}
      {!isOpen && (
        <button
          onClick={onToggle}
          aria-label="Open NEUROSTAGE AI Medical Assistant"
          title="Open NEUROSTAGE AI Medical Assistant"
          style={{
            position: 'fixed',
            bottom: '22px',
            right: '22px',
            zIndex: 9999,
            width: '52px',
            height: '52px',
            borderRadius: '50%',
            backgroundColor: '#0284c7',
            color: '#ffffff',
            border: 'none',
            boxShadow: '0 8px 24px rgba(2, 132, 199, 0.45)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.06)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          <Bot size={26} color="#ffffff" />
          <span style={{
            position: 'absolute',
            top: '-2px',
            right: '-2px',
            backgroundColor: '#ef4444',
            color: '#ffffff',
            fontSize: '0.65rem',
            fontWeight: 800,
            width: '18px',
            height: '18px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px solid #ffffff'
          }}>
            1
          </span>
        </button>
      )}

      {/* 2. CHATBOT WINDOW */}
      {isOpen && (
        <div
          role="dialog"
          aria-label="NEUROSTAGE AI Medical Assistant Window"
          style={{
            position: 'fixed',
            bottom: '22px',
            right: '22px',
            zIndex: 9999,
            width: '410px',
            maxWidth: 'calc(100vw - 24px)',
            height: '620px',
            maxHeight: 'calc(100vh - 44px)',
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            boxShadow: '0 20px 40px -8px rgba(15, 23, 42, 0.25), 0 0 0 1px rgba(15, 23, 42, 0.08)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            fontFamily: 'inherit',
            animation: 'fadeInUp 0.2s ease-out'
          }}
        >
          {/* Top Header */}
          <div style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            color: '#ffffff',
            padding: '14px 18px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexShrink: 0
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                backgroundColor: 'rgba(2, 132, 199, 0.25)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Bot size={20} color="#38bdf8" />
              </div>
              <div>
                <div style={{ fontSize: '0.94rem', fontWeight: 800, letterSpacing: '-0.01em', color: '#ffffff' }}>
                  NEUROSTAGE AI
                </div>
                <div style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 500 }}>
                  Medical Assistant
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                onClick={handleClearChat}
                title="Clear chat session"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  padding: '6px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                <RotateCcw size={15} />
              </button>
              <button
                onClick={onToggle}
                aria-label="Close assistant"
                title="Close chat"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  padding: '6px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Subheader Notice */}
          <div style={{
            backgroundColor: '#f8fafc',
            borderBottom: '1px solid #e2e8f0',
            padding: '7px 14px',
            fontSize: '0.72rem',
            color: '#64748b',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span>Medical information only — not a clinical diagnosis.</span>
            {mriContext && (
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                color: '#0284c7',
                fontWeight: 600,
                fontSize: '0.7rem'
              }}>
                <BrainCircuit size={12} />
                <span>MRI Scan Linked</span>
              </span>
            )}
          </div>

          {/* Messages Scroll Area */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '16px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            backgroundColor: '#ffffff'
          }}>
            {messages.map((m) => {
              const isUser = m.sender === 'user';
              return (
                <div
                  key={m.id}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isUser ? 'flex-end' : 'flex-start',
                    maxWidth: '100%'
                  }}
                >
                  <div style={{
                    display: 'flex',
                    gap: '8px',
                    alignItems: 'flex-start',
                    flexDirection: isUser ? 'row-reverse' : 'row',
                    maxWidth: '92%'
                  }}>
                    {/* Avatar */}
                    <div style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      backgroundColor: isUser ? '#0284c7' : '#f1f5f9',
                      border: isUser ? 'none' : '1px solid #cbd5e1',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      marginTop: '2px'
                    }}>
                      {isUser ? <User size={15} color="#ffffff" /> : <Bot size={15} color="#0284c7" />}
                    </div>

                    {/* Bubble */}
                    <div style={{
                      backgroundColor: isUser ? '#f0f9ff' : '#f8fafc',
                      color: isUser ? '#0f172a' : '#1e293b',
                      border: isUser ? '1px solid #bae6fd' : '1px solid #e2e8f0',
                      borderRadius: isUser ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                      padding: '12px 14px',
                      fontSize: '0.84rem',
                      lineHeight: 1.5,
                      wordBreak: 'break-word',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
                    }}>
                      {formatMessageText(m.text)}

                      {/* Sources pill container if provided */}
                      {m.sources && m.sources.length > 0 && (
                        <div style={{
                          marginTop: '10px',
                          paddingTop: '8px',
                          borderTop: '1px solid #e2e8f0',
                          fontSize: '0.72rem',
                          color: '#64748b'
                        }}>
                          <div style={{ fontWeight: 600, marginBottom: '4px', color: '#475569' }}>
                            Reputable Sources:
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                            {m.sources.map((s, sIdx) => (
                              <div key={sIdx} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <ExternalLink size={11} color="#0284c7" />
                                {s.url ? (
                                  <a
                                    href={s.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ color: '#0284c7', textDecoration: 'none', fontWeight: 500 }}
                                  >
                                    {s.name}
                                  </a>
                                ) : (
                                  <span>{s.name}</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <span style={{
                    fontSize: '0.65rem',
                    color: '#94a3b8',
                    marginTop: '3px',
                    marginRight: isUser ? '36px' : '0',
                    marginLeft: isUser ? '0' : '36px'
                  }}>
                    {m.timestamp}
                  </span>
                </div>
              );
            })}

            {/* Loading / Typing Animation */}
            {loading && (
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <div style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: '#f1f5f9',
                  border: '1px solid #cbd5e1',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Bot size={15} color="#0284c7" />
                </div>
                <div style={{
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  padding: '10px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>
                    Consulting medical evidence base...
                  </span>
                  <div style={{ display: 'flex', gap: '3px' }}>
                    <span className="typing-dot" style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#0284c7' }} />
                    <span className="typing-dot" style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#0284c7', animationDelay: '0.2s' }} />
                    <span className="typing-dot" style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#0284c7', animationDelay: '0.4s' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Starter Suggested Questions (shown when conversation is new) */}
          {messages.length <= 2 && !loading && (
            <div style={{
              padding: '8px 14px',
              borderTop: '1px solid #f1f5f9',
              backgroundColor: '#fafafa',
              flexShrink: 0
            }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748b', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <HelpCircle size={12} color="#0284c7" />
                <span>Suggested Questions:</span>
              </div>
              <div style={{
                display: 'flex',
                gap: '6px',
                overflowX: 'auto',
                paddingBottom: '4px',
                scrollbarWidth: 'none'
              }}>
                {STARTER_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(q)}
                    style={{
                      whiteSpace: 'nowrap',
                      backgroundColor: '#ffffff',
                      border: '1px solid #cbd5e1',
                      borderRadius: '14px',
                      padding: '4px 10px',
                      fontSize: '0.72rem',
                      color: '#0f172a',
                      cursor: 'pointer',
                      flexShrink: 0,
                      transition: 'all 0.15s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#0284c7';
                      e.currentTarget.style.backgroundColor = '#f0f9ff';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#cbd5e1';
                      e.currentTarget.style.backgroundColor = '#ffffff';
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat Input Container */}
          <div style={{
            padding: '12px 14px',
            borderTop: '1px solid #e2e8f0',
            backgroundColor: '#ffffff',
            flexShrink: 0
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '24px',
              padding: '6px 12px',
              transition: 'border-color 0.15s'
            }}>
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a medical or MRI staging question..."
                disabled={loading}
                style={{
                  flex: 1,
                  border: 'none',
                  outline: 'none',
                  backgroundColor: 'transparent',
                  fontSize: '0.84rem',
                  color: '#0f172a',
                  fontFamily: 'inherit'
                }}
              />
              <button
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || loading}
                aria-label="Send message"
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  border: 'none',
                  backgroundColor: inputValue.trim() && !loading ? '#0284c7' : '#e2e8f0',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: inputValue.trim() && !loading ? 'pointer' : 'not-allowed',
                  transition: 'all 0.15s',
                  flexShrink: 0
                }}
              >
                <Send size={14} />
              </button>
            </div>

            {/* Bottom Disclaimer Banner */}
            <div style={{
              fontSize: '0.68rem',
              color: '#94a3b8',
              textAlign: 'center',
              marginTop: '8px',
              lineHeight: 1.35
            }}>
              Medical information only — not a diagnosis. Consult a qualified healthcare professional.
            </div>
          </div>
        </div>
      )}
    </>
  );
}
