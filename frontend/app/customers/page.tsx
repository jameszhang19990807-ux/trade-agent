'use client';

import { useState, useEffect } from 'react';

interface Customer {
  id: number;
  whatsapp_number: string;
  name: string;
  country: string;
  pipeline_stage: string;
  total_inquiries: number;
  total_orders: number;
  total_value_usd: number;
  last_contact_at: string;
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [stageFilter, setStageFilter] = useState('');

  const fetchData = () => {
    const url = stageFilter ? `/api/customers?stage=${stageFilter}&limit=100` : '/api/customers?limit=100';
    fetch(url)
      .then(r => r.json())
      .then(d => { setCustomers(d.customers || []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [stageFilter]);

  if (loading) return <div style={{ padding: 40 }}>Loading...</div>;

  return (
    <div>
      <h1 className="page-title">Customers</h1>
      <p className="page-subtitle">All leads and customers tracked in the system</p>

      <div className="mb-4">
        <select
          className="stage-select"
          value={stageFilter}
          onChange={e => setStageFilter(e.target.value)}
          style={{ padding: '8px 14px', fontSize: 14 }}
        >
          <option value="">All Stages</option>
          <option value="new_lead">New Lead</option>
          <option value="replied">Replied</option>
          <option value="deep_talk">Deep Talk</option>
          <option value="sample_trial">Sample / Trial</option>
          <option value="formal_order">Formal Order</option>
          <option value="won">Won</option>
          <option value="lost">Lost</option>
          <option value="dormant">Dormant</option>
        </select>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {customers.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#9A9AA0' }}>No customers found</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #EBEBEB' }}>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: 12, fontWeight: 600, color: '#9A9AA0' }}>Name</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: 12, fontWeight: 600, color: '#9A9AA0' }}>Country</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: 12, fontWeight: 600, color: '#9A9AA0' }}>Stage</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: 12, fontWeight: 600, color: '#9A9AA0' }}>Inquiries</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: 12, fontWeight: 600, color: '#9A9AA0' }}>Orders</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: 12, fontWeight: 600, color: '#9A9AA0' }}>Value</th>
                <th style={{ textAlign: 'left', padding: '14px 20px', fontSize: 12, fontWeight: 600, color: '#9A9AA0' }}>Last Contact</th>
              </tr>
            </thead>
            <tbody>
              {customers.map(c => (
                <tr key={c.id} style={{ borderBottom: '1px solid #F5F5F5' }}>
                  <td style={{ padding: '14px 20px', fontSize: 14, fontWeight: 500 }}>{c.name}</td>
                  <td style={{ padding: '14px 20px', fontSize: 13 }}>{c.country || '-'}</td>
                  <td style={{ padding: '14px 20px' }}>
                    <span className={`badge ${
                      c.pipeline_stage === 'won' ? 'badge-green' :
                      c.pipeline_stage === 'lost' ? 'badge-red' :
                      c.pipeline_stage === 'new_lead' ? 'badge-gray' :
                      'badge-blue'
                    }`}>
                      {c.pipeline_stage}
                    </span>
                  </td>
                  <td style={{ padding: '14px 20px', fontSize: 13 }}>{c.total_inquiries}</td>
                  <td style={{ padding: '14px 20px', fontSize: 13 }}>{c.total_orders}</td>
                  <td style={{ padding: '14px 20px', fontSize: 13 }}>${c.total_value_usd?.toLocaleString() || 0}</td>
                  <td style={{ padding: '14px 20px', fontSize: 12, color: '#9A9AA0' }}>
                    {c.last_contact_at ? new Date(c.last_contact_at).toLocaleDateString() : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
