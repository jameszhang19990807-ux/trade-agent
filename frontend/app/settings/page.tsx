'use client';

import { useState, useEffect } from 'react';

interface SettingItem {
  key: string;
  label: string;
  value: string;
  masked: string;
  is_set: boolean;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingItem[]>([]);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [showValues, setShowValues] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetch('/api/settings')
      .then((r) => r.json())
      .then((data) => {
        setSettings(data.settings || []);
      });
  }, []);

  const handleEdit = (key: string, value: string) => {
    setEditing((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    const changed: Record<string, string> = {};
    for (const item of settings) {
      if (editing[item.key] !== undefined && editing[item.key] !== item.value) {
        changed[item.key] = editing[item.key];
      }
    }
    if (Object.keys(changed).length === 0) {
      setMessage('No changes to save');
      return;
    }

    setSaving(true);
    try {
      const resp = await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: changed }),
      });
      const data = await resp.json();
      if (data.status === 'ok') {
        setMessage('Saved! Credentials updated and active.');
        // Refresh
        const reload = await fetch('/api/settings');
        const reloaded = await reload.json();
        setSettings(reloaded.settings || []);
        setEditing({});
      } else {
        setMessage('Save failed');
      }
    } catch {
      setMessage('Network error');
    }
    setSaving(false);
    setTimeout(() => setMessage(''), 4000);
  };

  const getInputType = (key: string) => {
    return 'password';
  };

  const descriptions: Record<string, string> = {
    whatsapp_phone_number_id:
      'Found in Meta Business App → WhatsApp → API Setup. Looks like 123456789012345.',
    whatsapp_token:
      'Generate in Meta Business App → WhatsApp → API Setup → Temporary Access Token.',
    whatsapp_verify_token:
      'A secret string you choose. Must match the Webhook verify token in Meta App settings.',
    deepseek_api_key:
      'Get from platform.deepseek.com → API Keys. Used for AI intent recognition and replies.',
    agent_name: 'The name your customers see when the AI replies (e.g. "Lisa from Sales").',
    auto_reply_enabled: 'Set to "true" to let AI auto-reply, "false" to only log messages.',
  };

  return (
    <div>
      <h1>Settings</h1>
      <p className="section-desc">
        Configure WhatsApp and AI credentials. You control all your own data — nothing is shared.
      </p>

      {message && (
        <div className={`alert ${message.startsWith('Saved') ? 'alert-success' : 'alert-info'}`}>
          {message}
        </div>
      )}

      <div className="settings-list">
        {settings.map((item) => (
          <div key={item.key} className="setting-card">
            <div className="setting-header">
              <h3>{item.label}</h3>
              {item.is_set && (
                <span className="badge badge-set">Configured</span>
              )}
              {!item.is_set && (
                <span className="badge badge-empty">Not set</span>
              )}
            </div>
            <p className="setting-desc">{descriptions[item.key] || ''}</p>
            <div className="setting-input-row">
              <input
                type={
                  showValues[item.key]
                    ? 'text'
                    : 'password'
                }
                className="setting-input"
                placeholder={item.is_set ? '•••••••• (hidden)' : 'Paste your key here...'}
                value={editing[item.key] !== undefined ? editing[item.key] : ''}
                onChange={(e) => handleEdit(item.key, e.target.value)}
              />
              <button
                type="button"
                className="btn-ghost btn-sm"
                onClick={() =>
                  setShowValues((prev) => ({
                    ...prev,
                    [item.key]: !prev[item.key],
                  }))
                }
              >
                {showValues[item.key] ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="settings-actions">
        <button className="btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      <div className="settings-help">
        <h3>How to get WhatsApp credentials</h3>
        <ol>
          <li>Go to <a href="https://developers.facebook.com" target="_blank">developers.facebook.com</a> → Create App → Type: "Business"</li>
          <li>Add "WhatsApp" product to the app</li>
          <li>Under API Setup, copy your <strong>Phone Number ID</strong></li>
          <li>Generate a <strong>Temporary Access Token</strong> (lasts 24h, can extend later)</li>
          <li>Set Webhook URL: <code>https://trade-agent-backend.onrender.com/webhook/whatsapp</code></li>
          <li>Set Verify Token to whatever you entered above</li>
          <li>Paste both credentials here and Save</li>
        </ol>
      </div>
    </div>
  );
}
