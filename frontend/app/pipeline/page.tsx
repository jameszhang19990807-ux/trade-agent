'use client';

import { useState, useEffect } from 'react';

interface CustomerCard {
  id: number;
  whatsapp_number: string;
  name: string;
  country: string;
  pipeline_stage: string;
  total_inquiries: number;
  last_contact_at: string;
}

interface PipelineData {
  customers: CustomerCard[];
}

const PIPELINE_STAGES = [
  { key: 'new_lead', label: 'New Lead', color: 'badge-gray' },
  { key: 'replied', label: 'Replied', color: 'badge-blue' },
  { key: 'deep_talk', label: 'Deep Talk', color: 'badge-yellow' },
  { key: 'sample_trial', label: 'Sample / Trial', color: 'badge-yellow' },
  { key: 'formal_order', label: 'Formal Order', color: 'badge-green' },
  { key: 'won', label: 'Won', color: 'badge-green' },
  { key: 'lost', label: 'Lost', color: 'badge-red' },
  { key: 'dormant', label: 'Dormant', color: 'badge-gray' },
];

export default function PipelinePage() {
  const [customers, setCustomers] = useState<CustomerCard[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    fetch('/api/customers?limit=200')
      .then(r => r.json())
      .then(d => { setCustomers(d.customers || []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleStageChange = async (customerId: number, newStage: string) => {
    await fetch(`/api/customers/${customerId}/stage?stage=${newStage}`, { method: 'POST' });
    fetchData();
  };

  if (loading) return <div style={{ padding: 40 }}>Loading...</div>;

  return (
    <div>
      <h1 className="page-title">Pipeline</h1>
      <p className="page-subtitle">Drag-ready kanban view of all leads</p>

      <div style={{ display: 'flex', gap: 16, overflowX: 'auto', paddingBottom: 20 }}>
        {PIPELINE_STAGES.map(stage => {
          const stageCustomers = customers.filter(c => c.pipeline_stage === stage.key);
          return (
            <div key={stage.key} className="pipeline-column">
              <div className="flex-center" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{stage.label}</span>
                <span className={`badge ${stage.color}`}>{stageCustomers.length}</span>
              </div>
              {stageCustomers.map(c => (
                <div key={c.id} className="pipeline-card">
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{c.name}</div>
                  <div style={{ fontSize: 11, color: '#9A9AA0', marginBottom: 6 }}>
                    {c.country} &middot; {c.total_inquiries} inquiries
                  </div>
                  <select
                    className="stage-select"
                    value={c.pipeline_stage}
                    onChange={e => handleStageChange(c.id, e.target.value)}
                  >
                    {PIPELINE_STAGES.map(s => (
                      <option key={s.key} value={s.key}>{s.label}</option>
                    ))}
                  </select>
                </div>
              ))}
              {stageCustomers.length === 0 && (
                <div style={{ padding: 20, textAlign: 'center', color: '#CCC', fontSize: 12 }}>Empty</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
