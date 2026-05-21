'use client';

import { useState, useEffect } from 'react';

interface PipelineStat {
  stage: string;
  count: number;
}

interface ConversationRow {
  id: number;
  customer_name: string;
  status: string;
  intent_code: string;
  auto_round_count: number;
  last_message_preview: string;
  is_human_handling: boolean;
  updated_at: string;
}

interface DashboardData {
  total_leads: number;
  total_conversations: number;
  auto_reply_rate: number;
  conversion_rate: number;
  pipeline: PipelineStat[];
  recent_conversations: ConversationRow[];
}

const STAGE_LABELS: Record<string, string> = {
  new_lead: 'New Lead',
  replied: 'Replied',
  deep_talk: 'Deep Talk',
  sample_trial: 'Sample',
  formal_order: 'Order',
  won: 'Won',
  lost: 'Lost',
  dormant: 'Dormant',
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/dashboard/overview')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: 40 }}>Loading...</div>;
  if (!data) return <div style={{ padding: 40 }}>Failed to load dashboard. Is backend running?</div>;

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">Real-time trade inquiry overview</p>

      {/* Stats Row */}
      <div className="grid-4 mb-4">
        <div className="card stat-card">
          <div className="stat-label">Total Leads</div>
          <div className="stat-value">{data.total_leads}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Conversations</div>
          <div className="stat-value">{data.total_conversations}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Auto-Reply Rate</div>
          <div className="stat-value">{data.auto_reply_rate}%</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Conversion Rate</div>
          <div className="stat-value">{data.conversion_rate}%</div>
        </div>
      </div>

      <div className="grid-2">
        {/* Pipeline Summary */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Pipeline</h3>
          {data.pipeline.length === 0 ? (
            <p style={{ color: '#9A9AA0', fontSize: 13 }}>No leads yet</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.pipeline.map(p => (
                <div key={p.stage} className="flex-center" style={{ justifyContent: 'space-between' }}>
                  <span className="flex-center gap-2">
                    <span style={{ fontSize: 13, fontWeight: 500 }}>
                      {STAGE_LABELS[p.stage] || p.stage}
                    </span>
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{p.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Conversations */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Recent Conversations</h3>
          {data.recent_conversations.length === 0 ? (
            <p style={{ color: '#9A9AA0', fontSize: 13 }}>No conversations yet</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.recent_conversations.slice(0, 8).map(c => (
                <div
                  key={c.id}
                  className="flex-center"
                  style={{ justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #F5F5F5' }}
                >
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{c.customer_name}</div>
                    <div style={{ fontSize: 11, color: '#9A9AA0' }}>
                      {c.last_message_preview?.slice(0, 60) || 'No messages'}
                    </div>
                  </div>
                  <div className="flex-center gap-2">
                    {c.is_human_handling && <span className="badge badge-red">Human</span>}
                    {c.intent_code && (
                      <span className="badge badge-blue">{c.intent_code.replace('_', ' ')}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
