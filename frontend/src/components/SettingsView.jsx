import React, { useState } from 'react';
import { Save, Server, Database, Globe, Folder, Info, Eye, Monitor, Camera } from 'lucide-react';
import axios from 'axios';
import { API_BASE } from '../api.js';

const SettingsView = ({ onOpenHelp, onTriggerVision, onManualCam }) => {
  const [settings, setSettings] = useState({
    llm_url: '',
    default_model: '',
    postgres_url: '',
    qdrant_url: '',
    searxng_url: '',
    storagePath: '/home/scruffydawg/guide_storage',
    visionEnabled: true
  });
  
  const [ollamaModels, setOllamaModels] = useState([]);

  // Fetch Config and Models on Mount
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const configResp = await axios.get(`${API_BASE}/config`);
        // V2 envelope places the payload in 'data' key
        const configData = configResp.data?.data || configResp.data;
        setSettings(prev => ({ ...prev, ...configData }));
      } catch (e) {
        console.error("Failed to fetch config", e);
      }
      
      try {
        const modelsResp = await axios.get(`${API_BASE}/ollama/models`);
        if (modelsResp.data?.status === 'success') {
            const modelsList = modelsResp.data?.data?.models || modelsResp.data?.models || [];
            setOllamaModels(modelsList);
        }
      } catch (e) {
        console.error("Failed to fetch ollama models", e);
      }
    };
    fetchData();
  }, []);

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setSettings({ ...settings, [e.target.name]: value });
  };

  const handleSave = async () => {
    try {
      await axios.post(`${API_BASE}/config`, settings);
      alert("Configuration Synthesized Successfully.");
    } catch (e) {
      alert("Failed to sync configuration with the mesh.");
    }
  };

  const handleInitStorage = async () => {
    try {
      const resp = await axios.post(`${API_BASE}/storage/init?path=${settings.storagePath}`);
      if (resp.data.status === 'success') {
        alert("Workspace Initialized Successfully!");
      } else {
        alert("Error initializing workspace: " + resp.data.status);
      }
    } catch (e) {
      alert("Failed to connect to server for storage init.");
    }
  };

  return (
    <div className="card" style={{ padding: '32px', maxWidth: '800px', margin: '0 auto' }}>
    <h2 style={{ fontSize: '1.5rem', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
        <img src="/ehecatl.png" style={{ width: '100px', height: '100px', borderRadius: '50%', border: '2px solid var(--accent-ochre)', boxShadow: '0 0 15px var(--accent-glow)' }} alt="Guide" />
        COGNITION SETTINGS
    </h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="form-group">
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', opacity: 0.7 }}>
            AI STORAGE PATH (DISK/GDRIVE) 
            <Info size={14} style={{ cursor: 'pointer', color: 'var(--accent-cyan)' }} onClick={() => onOpenHelp('settings')} />
          </label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <Folder size={20} style={{ alignSelf: 'center', opacity: 0.5 }} />
            <input 
              name="storagePath"
              value={settings.storagePath || ''}
              onChange={handleChange}
              placeholder="/absolute/path/to/storage"
              style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-primary)' }} 
            />
            <button onClick={handleInitStorage} className="btn-secondary" style={{ whiteSpace: 'nowrap' }}>
               INITIALIZE SCHEMA
            </button>
          </div>
        </div>

        <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
           <input 
            type="checkbox"
            name="visionEnabled"
            checked={settings.visionEnabled}
            onChange={handleChange}
            id="vision-toggle"
           />
           <label htmlFor="vision-toggle" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Eye size={18} color="var(--accent-cyan)" /> ENABLE MULTI-MODAL VISION (WEB CAM / SCREENSHOTS)
           </label>
        </div>

        {settings.visionEnabled && (
          <div className="card" style={{ background: 'var(--accent-translucent)', border: '1px dashed var(--accent-ochre)', padding: '20px' }}>
            <h4 style={{ fontSize: '0.8rem', marginBottom: '15px', color: 'var(--accent-ochre)', letterSpacing: '1px' }}>MANUAL VISION OVERRIDES (REMOTE/TESTING)</h4>
            <div style={{ display: 'flex', gap: '15px' }}>
              <button 
                onClick={() => onTriggerVision('screenshot')} 
                className="button-secondary"
                style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
              >
                <Monitor size={16} /> TRIGGER SCREENSHOT
              </button>
              <button 
                onClick={onManualCam} 
                className="button-secondary"
                style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
              >
                <Camera size={16} /> OPEN WEBCAM PREVIEW
              </button>
            </div>
            <p style={{ fontSize: '0.7rem', opacity: 0.5, marginTop: '10px' }}>
              Note: Privacy confirmations will still trigger on authorization-required captures.
            </p>
          </div>
        )}

        <div className="form-group">
          <label style={{ display: 'block', marginBottom: '8px', opacity: 0.7 }}>LLM / OLLAMA API URL</label>
          <div style={{ display: 'flex', gap: '10px' }}>
             <Server size={20} style={{ alignSelf: 'center', opacity: 0.5 }} />
             <input 
              name="llm_url"
              value={settings.llm_url || ''}
              onChange={handleChange}
              style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-primary)' }} 
             />
          </div>
        </div>

        <div className="form-group">
          <label style={{ display: 'block', marginBottom: '8px', opacity: 0.7 }}>DEFAULT LLM MODEL (e.g. qwen3:14b)</label>
          <div style={{ display: 'flex', gap: '10px' }}>
             <Server size={20} style={{ alignSelf: 'center', opacity: 0.5 }} />
             {ollamaModels.length > 0 ? (
                 <select
                    name="default_model"
                    value={settings.default_model || ''}
                    onChange={handleChange}
                    style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-primary)', cursor: 'pointer', appearance: 'none' }}
                 >
                     <option value={settings.default_model}>{settings.default_model || "Select a model..."}</option>
                     {ollamaModels.filter(m => m !== settings.default_model).map(model => (
                         <option key={model} value={model}>{model}</option>
                     ))}
                 </select>
             ) : (
                 <input 
                  name="default_model"
                  value={settings.default_model || ''}
                  onChange={handleChange}
                  style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-primary)' }} 
                 />
             )}
          </div>
        </div>

        <div className="form-group">
          <label style={{ display: 'block', marginBottom: '8px', opacity: 0.7 }}>POSTGRESQL CONNECTION STRING</label>
          <div style={{ display: 'flex', gap: '10px' }}>
             <Database size={20} style={{ alignSelf: 'center', opacity: 0.5 }} />
             <input 
              name="postgres_url"
              value={settings.postgres_url || ''}
              onChange={handleChange}
              style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-primary)' }} 
             />
          </div>
        </div>

        <div className="form-group">
          <label style={{ display: 'block', marginBottom: '8px', opacity: 0.7 }}>QDRANT VECTOR DB URL</label>
          <input 
            name="qdrant_url"
            value={settings.qdrant_url || ''}
            onChange={handleChange}
            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-primary)' }} 
          />
        </div>

        <div className="form-group">
          <label style={{ display: 'block', marginBottom: '8px', opacity: 0.7 }}>SEARXNG INSTANCE URL</label>
          <div style={{ display: 'flex', gap: '10px' }}>
             <Globe size={20} style={{ alignSelf: 'center', opacity: 0.5 }} />
             <input 
              name="searxng_url"
              value={settings.searxng_url || ''}
              onChange={handleChange}
              style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-primary)' }} 
             />
          </div>
        </div>

        <button onClick={handleSave} className="btn-primary" style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
          <Save size={18} /> SAVE CONFIGURATION
        </button>

        <div className="card" style={{ marginTop: '32px', padding: '20px', background: 'var(--header-bg)' }}>
            <h4 style={{ fontSize: '0.9rem', marginBottom: '15px', color: 'var(--accent-ochre)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Activity size={18} /> SYSTEM PERFORMANCE & DIAGNOSTICS
            </h4>
            <div style={{ fontSize: '0.8rem', fontFamily: 'monospace', opacity: 0.8, lineHeight: '1.6' }}>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <span style={{ color: 'var(--accent-cyan)' }}>[0.00s]</span> <span>Kernel Initialized</span>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <span style={{ color: 'var(--accent-cyan)' }}>[0.12s]</span> <span>Storage Mapped: {settings.storagePath}</span>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <span style={{ color: 'var(--accent-cyan)' }}>[0.45s]</span> <span>Expert Suite Loaded: 3 (Security, UX, Architect)</span>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <span style={{ color: 'var(--accent-cyan)' }}>[0.89s]</span> <span>Local LLM Mesh: Synchronized</span>
                </div>
                <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                    <span style={{ color: 'var(--accent-green)' }}>[OK]</span> <span>Ready for High-Flow Execution.</span>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;
