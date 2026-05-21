'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Conv {
  id: number;
  customer_name: string;
  status: string;
  is_human_handling: boolean;
  intent_code: string;
  auto_round_count: number;
  last_message_preview: string;
  updated_at: string;
}

export default function ConversationsPage() {
  const [convs, setConvs] = useState<Conv[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/dashboard/overview')
      .then(r => r.json())
      .then(d => { setConvs(d.recent_conversations || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: 40 }}>Loading...</div>;

  return (
    <div>
      <h1 className="page-title">Conversations</h1>
      <p className="page-subtitle">All customer conversations from WhatsApp</p>

      <div className="card" style={{ padding: 0 }}>
        {convs.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#9A9AA0' }}>No conversations yet</div>
        ) : (
          convs.map(c => (
            <Link key={c.id} href={`/conversations/${c.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="conversation-row">
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 2 }}>{c.customer_name}</div>
                  <div style={{ fontSize: 12, color: '#9A9AA0' }}>
                    {c.last_message_preview?.slice(0, 80) || 'No messages'}
                  </div>
                </div>
                <div className="flex-center gap-2">
                  <span style={{ fontSize: 12, color: '#9A9AA0' }}>Rounds: {c.auto_round_count}</span>
                  {c.is_human_handling && <span className="badge badge-red">Human</span>}
                  <span className={`badge ${c.status === 'active' ? 'badge-green' : 'badge-yellow'}`}>
                    {c.status}
                  </span>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
