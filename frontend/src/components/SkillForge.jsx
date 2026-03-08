import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Hammer, Zap, Search, Cpu, Code, Shield, ChevronRight, 
  Terminal, Package, Globe, Plus, Trash2, CheckCircle2 
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import { API_BASE } from '../api.js';

const SkillForge = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: "WELCOME TO THE FORGE. I am Guide. I will help you synthesize new capabilities for our swarm. What shall we manifest today?" }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [preview, setPreview] = useState({
        name: 'New Manifestation',
        type: 'Skill', 
        status: 'Conceptualizing',
        dependencies: [],
        architecture: '',
        sources: []
    });
    const chatEndRef = useRef(null);

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;
        
        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const resp = await axios.post(`${API_BASE}/forge/interview`, { 
                prompt: input,
                history: messages,
                current_preview: preview
            });
            
            setMessages(prev => [...prev, { role: 'assistant', content: resp.data.response }]);
            if (resp.data.preview_update) {
                setPreview(resp.data.preview_update);
            }
        } catch (error) {
            setMessages(prev => [...prev, { role: 'assistant', content: "INTERRUPTION: Swarm synchronization lost. Seeking re-connection..." }]);
        }
        setLoading(false);
    };

    const handleAssemble = async () => {
        setLoading(true);
        try {
            const resp = await axios.post(`${API_BASE}/forge/assemble`, { preview });
            alert(`MANIFESTATION COMPLETE: ${resp.data.message}`);
        } catch (error) {
            alert("FORGE ERROR: The architecture requires re-alignment.");
        }
        setLoading(false);
    };

    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(400px, 1fr) 450px', gap: '30px', height: '100%', overflow: 'hidden' }}>
            {/* Interview Panel */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', position: 'relative', overflow: 'hidden' }}>
                <div style={{ padding: '25px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '20px', background: 'var(--header-bg)' }}>
                    <img 
                        src="/ehecatl.png" 
                        style={{ width: '100px', height: '100px', borderRadius: '50%', border: '3px solid var(--accent-ochre)', boxShadow: '0 0 20px var(--accent-glow)' }}
                        alt="Guide Mascot"
                    />
                    <div>
                        <h2 style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '1px' }}>GUIDE'S FORGE</h2>
                        <p style={{ fontSize: '0.75rem', opacity: 0.5, letterSpacing: '1.5px', textTransform: 'uppercase' }}>Guided Synthesis Protocol</p>
                    </div>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', padding: '25px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <AnimatePresence>
                        {messages.map((msg, i) => (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                key={i}
                                style={{
                                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                    maxWidth: '80%',
                                    background: msg.role === 'user' ? 'var(--user-bubble-bg)' : 'var(--accent-translucent)',
                                    color: msg.role === 'user' ? 'var(--user-bubble-text)' : 'var(--text-primary)',
                                    padding: '16px 22px',
                                    borderRadius: '16px',
                                    fontSize: '1rem',
                                    lineHeight: '1.6',
                                    border: msg.role === 'user' ? 'none' : '1px solid var(--border-color)',
                                    boxShadow: msg.role === 'user' ? 'var(--card-shadow)' : 'none'
                                }}
                            >
                                {msg.content}
                            </motion.div>
                        ))}
                    </AnimatePresence>
                    <div ref={chatEndRef} />
                </div>

                <div style={{ padding: '25px', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '15px', background: 'var(--header-bg)' }}>
                    <input 
                        className="input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Project your intent into the Forge..."
                        style={{ flex: 1, padding: '16px', borderRadius: '12px', fontSize: '1rem' }}
                    />
                    <button 
                        className="button-primary" 
                        onClick={handleSend}
                        disabled={loading}
                        style={{ padding: '0 25px', borderRadius: '12px', background: 'var(--accent-ochre)', color: 'var(--overlay-heavy-bg)' }}
                    >
                        {loading ? <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity }}><Zap size={22} /></motion.div> : <ChevronRight size={28} />}
                    </button>
                </div>
            </div>

            {/* Preview Panel */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                <div className="card" style={{ padding: '30px', border: '2px solid var(--accent-ochre)', boxShadow: 'var(--card-shadow)', background: 'var(--panel-bg)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                        <h3 style={{ fontSize: '0.8rem', opacity: 0.5, letterSpacing: '2.5px', fontWeight: 'bold' }}>FORGE DRAFT</h3>
                        <div style={{ fontSize: '0.7rem', padding: '5px 12px', borderRadius: '6px', background: 'var(--accent-ochre)', color: 'var(--overlay-heavy-bg)', fontWeight: '900' }}>{preview.status.toUpperCase()}</div>
                    </div>

                    <div style={{ marginBottom: '30px' }}>
                        <h2 style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--text-primary)', marginBottom: '8px' }}>{preview.name}</h2>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                           <span style={{ fontSize: '0.8rem', color: 'var(--accent-ochre)', fontWeight: '700' }}>#{preview.type}</span>
                           <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--border-color)' }}></div>
                           <span style={{ fontSize: '0.8rem', opacity: 0.5 }}>Guided Manifestation</span>
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                        <div style={{ background: 'var(--accent-translucent)', padding: '15px', borderRadius: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                                <Package size={16} color="var(--accent-cyan)" />
                                <span style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Dependencies</span>
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                                {preview.dependencies.length > 0 ? preview.dependencies.map(d => (
                                    <span key={d} style={{ fontSize: '0.7rem', padding: '2px 8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px' }}>{d}</span>
                                )) : <span style={{ fontSize: '0.7rem', opacity: 0.4 }}>No dependencies detected yet...</span>}
                            </div>
                        </div>

                        <div style={{ background: 'var(--accent-translucent)', padding: '15px', borderRadius: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                                <Terminal size={16} color="var(--accent-cyan)" />
                                <span style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Arch Proposal</span>
                            </div>
                            <pre style={{ fontSize: '0.75rem', margin: 0, opacity: 0.8, whiteSpace: 'pre-wrap' }}>
                                {preview.architecture || "Drafting implementation plan..."}
                            </pre>
                        </div>

                        <div style={{ background: 'var(--accent-translucent)', padding: '15px', borderRadius: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                                <Globe size={16} color="var(--accent-cyan)" />
                                <span style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>Research Sources</span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                                {preview.sources.map(s => (
                                    <span key={s} style={{ fontSize: '0.7rem', opacity: 0.6, overflow: 'hidden', textOverflow: 'ellipsis', background: 'var(--accent-translucent)', padding: '2px 8px', borderRadius: '4px' }}>• {s}</span>
                                ))}
                            </div>
                        </div>
                    </div>

                    <button 
                        className="button-primary" 
                        onClick={handleAssemble}
                        disabled={preview.status !== 'Ready' || loading}
                        style={{ width: '100%', marginTop: '30px', padding: '15px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}
                    >
                        {loading ? "PROCESSING..." : (
                            <>
                                <Zap size={18} /> ASSEMBLE SKILL
                            </>
                        )}
                    </button>
                    {preview.status !== 'Ready' && (
                        <p style={{ fontSize: '0.65rem', textAlign: 'center', marginTop: '10px', opacity: 0.5 }}>Forge requires user approval of architectural draft.</p>
                    )}
                </div>

                <div className="card" style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Shield size={16} color="var(--accent-green)" />
                        <span style={{ fontSize: '0.75rem', fontWeight: 'bold' }}>Safety Sandbox Active</span>
                    </div>
                    <p style={{ fontSize: '0.7rem', opacity: 0.6 }}>Skills are generated in `sandbox/` and require manual promotion to `src/skills/` after testing.</p>
                </div>
            </div>
        </div>
    );
};

export default SkillForge;
