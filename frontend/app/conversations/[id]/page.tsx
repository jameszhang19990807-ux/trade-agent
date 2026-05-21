'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';

interface Message {
  id: number;
  direction: 'inbound' | 'outbound';
  sender_name: string;
  content: string;
  is_auto_generated: boolean;
  created_at: string;
}

interface ConvDetail {
  id: number;
  customer: {
    id: number;
    name: string;
    country: string;
    pipeline_stage: string;
  };
  status: string;
  is_human_handling: boolean;
  intent_code: string;
  messages: Message[];
}

export default function ConversationDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [conv, setConv] = useState<ConvDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchConv = useCallback(() => {
    fetch(`/api/conversations/${id}`)
      .then(r => r.json())
      .then(d => { setConv(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [id]);

  useEffect(() => { fetchConv(); }, [fetchConv]);

  const handleTakeover = async () => {
    await fetch(`/api/conversations/${id}/takeover`, { method: 'POST' });
    fetchConv();
  };

  if (loading) return <div style={{ padding: 40 }}>Loading...</div>;
  if (!conv || (conv as any).error) return <div style={{ padding: 40 }}>Conversation not found</div>;

  return (
    <div>
      <div className="flex-center" style={{ justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <h1 className="page-title" style={{ marginBottom: 2 }}>{conv.customer.name}</h1>
          <p style={{ fontSize: 13, color: '#9A9AA0' }}>
            {conv.customer.country || 'Unknown'} &middot; Stage: {conv.customer.pipeline_stage}
            {conv.intent_code && <span> &middot; Intent: {conv.intent_code}</span>}
          </p>
        </div>
        <div className="flex-center gap-4">
          {conv.is_human_handling ? (
            <span className="badge badge-red">Human Handling</span>
          ) : (
            <button
              onClick={handleTakeover}
              style={{
                background: '#EF5350', color: '#FFF', border: 'none',
                borderRadius: 8, padding: '8px 18px', fontSize: 13, fontWeight: 500, cursor: 'pointer',
              }}
            >
              Take Over
            </button>
          )}
        </div>
      </div>

      <div className="chat-window">
        <div className="chat-messages">
          {conv.messages.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#9A9AA0', padding: 40 }}>No messages</div>
          ) : (
            conv.messages.map(m => (
              <div key={m.id} className={`chat-bubble ${m.direction}`}>
                <div className="chat-bubble-meta">
                  {m.sender_name} {m.is_auto_generated && '(auto)'}
                </div>
                <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>
              </div>
            ))
          )}
        </div>
        {conv.is_human_handling && (
          <div className="chat-input-area">
            <input type="text" placeholder="Type a reply... (WhatsApp API)" />
            <button>Send</button>
          </div>
        )}
      </div>
    </div>
  );
}
