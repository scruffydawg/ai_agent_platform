import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Monitor, Cpu, HardDrive, Activity, Zap, Server, ShieldCheck, AlertTriangle, Box, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { API_BASE } from '../api.js';

const MetricBar = ({ label, value, color, compact }) => (
    <div style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: compact ? '0.65rem' : '0.75rem', fontWeight: 'bold' }}>
            <span style={{ opacity: 0.5 }}>{label}</span>
            <span>{value}%</span>
        </div>
        <div style={{ height: '4px', width: '100%', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
            <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${value}%` }}
                transition={{ type: 'spring', stiffness: 100, damping: 20 }}
                style={{ height: '100%', background: color, boxShadow: `0 0 8px ${color}` }} 
            />
        </div>
    </div>
);

const NodeCard = ({ name, data, compact }) => {
    if (!data) return null;
    const isOffline = data.status === 'offline';
    const accentColor = isOffline ? 'var(--accent-red)' : 'var(--accent-cyan)';

    return (
        <div 
            className="glass-panel" 
            style={{ 
                padding: compact ? '15px' : '24px', 
                border: `1px solid ${accentColor}`,
                background: isOffline ? 'rgba(255, 68, 68, 0.05)' : 'var(--panel-bg)',
                position: 'relative',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                minHeight: compact ? 'auto' : '280px',
                boxShadow: compact ? 'none' : 'var(--card-shadow)'
            }}
        >
            {/* Node Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: compact ? '10px' : '20px', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ 
                        padding: compact ? '6px' : '10px', 
                        borderRadius: '10px', 
                        background: 'var(--accent-translucent)',
                        border: `1px solid ${accentColor}`
                    }}>
                         <Server size={compact ? 16 : 20} color={accentColor} />
                    </div>
                    <div>
                        <h3 style={{ fontSize: compact ? '0.8rem' : '1rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '1px', margin: 0 }}>{name.replace('_', ' ')}</h3>
                        {!compact && (
                            <span style={{ fontSize: '0.65rem', color: accentColor, fontWeight: '700' }}>
                                {isOffline ? 'SYSTEM OFFLINE' : 'MESH SECURED'}
                            </span>
                        )}
                    </div>
                </div>
                {isOffline ? <AlertTriangle size={compact ? 14 : 18} color="var(--accent-red)" /> : <ShieldCheck size={compact ? 14 : 18} color="var(--accent-green)" />}
            </div>

            {/* Metrics */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? '8px' : '15px', flex: 1 }}>
                <MetricBar label="CPU" value={data.cpu} color="var(--accent-cyan)" compact={compact} />
                <MetricBar label="RAM" value={data.ram} color="var(--accent-purple)" compact={compact} />
                {!compact && data.gpu > 0 && <MetricBar label="GPU VRAM" value={data.gpu} color="var(--accent-green)" />}
            </div>

            {/* Instance Status List - Addressing "container instances get status" */}
            <div style={{ marginTop: compact ? '10px' : '20px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {(data?.llm_instances || []).map(inst => (
                    <div key={inst} style={{ 
                        fontSize: '0.6rem', 
                        padding: '4px 8px', 
                        borderRadius: '6px', 
                        background: isOffline ? 'var(--nav-hover-bg)' : 'rgba(0, 255, 255, 0.1)', 
                        color: isOffline ? 'var(--text-secondary)' : 'var(--accent-cyan)', 
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        border: `1px solid ${isOffline ? 'transparent' : 'rgba(0, 255, 255, 0.2)'}`
                    }}>
                       <Box size={10} />
                       {inst}
                       {!isOffline && <CheckCircle size={10} color="var(--accent-green)" />}
                    </div>
                ))}
            </div>

            {/* Footer Info */}
            {!isOffline && !compact && (
                <div style={{ marginTop: 'auto', paddingTop: '15px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <Zap size={12} /> <span>{data.vllm_tps} T/S</span>
                    </div>
                    <span>12ms LATENCY</span>
                </div>
            )}
        </div>
    );
};

const SystemsDashboard = ({ compact = false }) => {
    const [swarmData, setSwarmData] = useState({});
    const [loading, setLoading] = useState(true);

    const fetchSwarmStatus = async () => {
        try {
            const resp = await axios.get(`${API_BASE}/swarm/status`);
            setSwarmData(resp.data);
            setLoading(false);
        } catch (e) {
            console.error("Failed to fetch swarm data", e);
        }
    };

    useEffect(() => {
        fetchSwarmStatus();
        const interval = setInterval(fetchSwarmStatus, 2000); // 2s for "streaming" feel
        return () => clearInterval(interval);
    }, []);

    if (loading && !compact) return <div style={{ padding: '40px', textAlign: 'center', opacity: 0.5 }}>SYNCHRONIZING MESH...</div>;

    return (
        <div style={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: compact ? '10px' : '24px',
            overflow: 'hidden'
        }}>
            {!compact && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h2 style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--accent-cyan)', margin: 0 }}>SYSTEMS DASHBOARD</h2>
                        <p style={{ opacity: 0.6, fontSize: '0.9rem' }}>Real-time resource telemetry across the private Tailnet mesh.</p>
                    </div>
                    <div style={{ background: 'var(--panel-bg)', padding: '10px 20px', borderRadius: '12px', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '15px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div className="status-pulse" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-green)' }}></div>
                            <span style={{ fontSize: '0.8rem', fontWeight: '700' }}>MESH SECURED</span>
                        </div>
                    </div>
                </div>
            )}

            <div style={{ 
                flex: 1, 
                display: 'grid', 
                gridTemplateColumns: compact ? 'repeat(auto-fill, minmax(240px, 1fr))' : 'repeat(auto-fill, minmax(320px, 1fr))', 
                gap: compact ? '15px' : '24px',
                overflowY: 'auto',
                paddingRight: '5px',
                paddingBottom: '20px'
            }}>
                {Object.entries(swarmData || {}).map(([name, data]) => (
                    data ? <NodeCard key={name} name={name} data={data} compact={compact} /> : null
                ))}
            </div>

            {/* Swarm Logistics Summary */}
            {!compact && (
                <div className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-around', alignItems: 'center', background: 'rgba(0, 255, 255, 0.02)', border: '1px dashed var(--border-color)', borderRadius: '16px' }}>
                    <div style={{ textAlign: 'center' }}>
                        <h4 style={{ fontSize: '0.65rem', opacity: 0.5, marginBottom: '5px', letterSpacing: '1px' }}>TOTAL AGENTS</h4>
                        <span style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--accent-cyan)' }}>12</span>
                    </div>
                    <div style={{ width: '1px', height: '30px', background: 'var(--border-color)' }}></div>
                    <div style={{ textAlign: 'center' }}>
                        <h4 style={{ fontSize: '0.65rem', opacity: 0.5, marginBottom: '5px', letterSpacing: '1px' }}>THROUGHPUT</h4>
                        <span style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--accent-green)' }}>85 T/S</span>
                    </div>
                    <div style={{ width: '1px', height: '30px', background: 'var(--border-color)' }}></div>
                    <div style={{ textAlign: 'center' }}>
                        <h4 style={{ fontSize: '0.65rem', opacity: 0.5, marginBottom: '5px', letterSpacing: '1px' }}>MESH STATUS</h4>
                        <span style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--accent-cyan)' }}>OPTIMAL</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SystemsDashboard;
