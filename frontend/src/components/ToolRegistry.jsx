import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Puzzle, Globe, Database, Monitor, FileText, Cpu, Eye, Mic, Speaker,
    Brain, Play, Mail, Server, Wrench, RefreshCw, Folder, Code, Save,
    X, Activity, Zap, BookOpen, Terminal, Table2, HelpCircle,
    MessageSquare, Send, ChevronUp, ChevronDown
} from 'lucide-react';
import { API_BASE } from '../api.js';

// ── Parser: extracts methods/params/returns/isAsync from Python source ────────
const parsePythonScript = (code, fallbackDesc) => {
    const lines = (code || '').split('\n');
    let classDesc = typeof fallbackDesc === 'string' ? fallbackDesc : 'Native Implementation Module.';
    const methods = [];
    let currentMethod = null;
    let inMethodDocstring = false;
    let docSection = null;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        const defMatch = line.match(/^\s*(?:async\s+)?def ([a-zA-Z0-9_]+)\(([^)]*)?/);
        if (defMatch) {
            if (currentMethod) methods.push(currentMethod);
            inMethodDocstring = false;
            docSection = null;
            const isAsync = /^\s*async\s+def/.test(line);
            const rawParams = (defMatch[2] || '')
                .split(',')
                .map(p => p.trim().split(':')[0].split('=')[0].trim())
                .filter(p => p && !['self', 'cls', '*args', '**kwargs', '*'].includes(p));
            if (!defMatch[1].startsWith('_')) {
                currentMethod = { name: defMatch[1], doc: '', params: rawParams, returns: '', isAsync };
            } else {
                currentMethod = null;
            }
            continue;
        }
        if (!currentMethod) continue;

        if (!inMethodDocstring) {
            if (trimmed.startsWith('"""') || trimmed.startsWith("'''")) {
                const quote = trimmed.startsWith('"""') ? '"""' : "'''";
                const rest = trimmed.slice(quote.length);
                const closeIdx = rest.indexOf(quote);
                if (closeIdx !== -1) {
                    currentMethod.doc = rest.slice(0, closeIdx).trim();
                    docSection = 'done';
                } else {
                    currentMethod.doc = rest.trim();
                    inMethodDocstring = true;
                    docSection = 'summary';
                    currentMethod._quote = quote;
                }
            } else if (trimmed !== '') {
                methods.push(currentMethod);
                currentMethod = null;
            }
        } else {
            const quote = currentMethod._quote || '"""';
            const closeIdx = trimmed.indexOf(quote);
            if (closeIdx !== -1) {
                inMethodDocstring = false;
                docSection = 'done';
                delete currentMethod._quote;
            } else if (/^Returns?:/i.test(trimmed)) {
                docSection = 'returns';
            } else if (/^(Args?|Parameters?|Params?):/i.test(trimmed)) {
                docSection = 'args';
            } else if (/^(Raises?|Example|Note|Todo):/i.test(trimmed)) {
                docSection = 'skip';
            } else if (docSection === 'returns' && trimmed !== '') {
                if (!currentMethod.returns) currentMethod.returns = trimmed.replace(/^[-*]\s*/, '');
                docSection = 'skip';
            } else if (docSection === 'summary' && trimmed !== '') {
                currentMethod.doc += ' ' + trimmed;
            }
        }
    }
    if (currentMethod) methods.push(currentMethod);
    if (classDesc) classDesc = classDesc.replace(/\s+/g, ' ').trim();
    methods.forEach(m => {
        if (m.doc) m.doc = m.doc.replace(/\s+/g, ' ').trim();
        if (m.returns) m.returns = m.returns.replace(/\s+/g, ' ').trim();
    });
    return { classDesc, methods };
};


// ── Contextual Help Data ───────────────────────────────────────────────────────
const HELP_DATA = {
    'CAPABILITY OVERVIEW': 'High-level summary of the tool\'s core purpose and capabilities.',
    'EXECUTION NODES': 'Specific Python methods the AI can call to perform actions. Each node includes parameters and return types.',
    'REFERENCE DOCS': 'Official documentation, API references, and external guides to help the agent use this tool effectively.',
    'CONNECTION CONFIG': 'Technical settings (paths, env vars, start commands) required to link the platform to this external service.',
    'API QUICK-COMMANDS': 'A cheat-sheet of the most relevant REST API endpoints for this hybrid service.',
    'HYBRID': 'A sophisticated integration combining native Python logic with an external MCP server or REST API.',
    'MCP': 'Model Context Protocol — a standardized protocol for connecting AI models to local data and tool servers.',
    'NATIVE SKILL': 'A pure Python capability built directly into the platform.',
    'CODE TOOL': 'A dynamically generated snippet of execution code, usually created during a canvas research session.'
};

// ── Shared card wrapper ────────────────────────────────────────────────────────
const SectionCard = ({ accentColor = 'var(--accent-cyan)', children, style = {} }) => (
    <div className="glass-panel" style={{
        borderTop: `3px solid ${accentColor}`,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        ...style
    }}>
        {children}
    </div>
);

const SectionHeader = ({ icon: Icon, title, color }) => (
    <div 
        title={HELP_DATA[title] || ''}
        style={{
            padding: '14px 22px',
            background: 'var(--header-bg)',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex', alignItems: 'center', gap: '10px',
            cursor: 'help'
        }}
    >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
            {Icon && <Icon size={18} color={color} />}
            <span style={{ fontSize: '0.8rem', fontWeight: '900', color, letterSpacing: '1.5px' }}>{title}</span>
        </div>
        <HelpCircle size={14} style={{ opacity: 0.3, color }} />
    </div>
);

const CodeRow = ({ label, value, valueColor = 'var(--accent-cyan)' }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
        <span style={{ fontSize: '0.6rem', fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '1.5px', opacity: 0.8 }}>{label}</span>
        <code style={{ 
            display: 'block', 
            fontSize: '0.78rem', 
            padding: '10px 14px', 
            borderRadius: '10px', 
            background: 'var(--nav-hover-bg)', 
            color: valueColor, 
            wordBreak: 'break-all', 
            lineHeight: 1.5,
            border: '1px solid var(--border-color)',
            boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)'
        }}>{value}</code>
    </div>
);

// ── Section: CAPABILITY OVERVIEW ──────────────────────────────────────────────
const OverviewSection = ({ tool, classDesc }) => {
    const color = tool.subtype === 'mcp' ? 'var(--accent-purple)' : tool.subtype === 'hybrid' ? 'var(--accent-ochre)' : 'var(--accent-cyan)';
    return (
        <SectionCard accentColor={color}>
            <SectionHeader icon={Puzzle} title="CAPABILITY OVERVIEW" color={color} />
            <div style={{ padding: '18px 22px' }}>
                <p style={{ margin: 0, lineHeight: 1.75, opacity: 0.9, fontSize: '0.95rem' }}>{classDesc}</p>
            </div>
        </SectionCard>
    );
};

// ── Section: EXECUTION NODES ──────────────────────────────────────────────────
const ExecutionNodesSection = ({ methods }) => (
    <SectionCard accentColor="#EAB308" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <SectionHeader icon={Zap} title="EXECUTION NODES" color="#EAB308" />
        <div style={{ display: 'flex', flexDirection: 'column' }}>
            {methods.map((m, i) => (
                <div key={i} style={{ 
                    borderBottom: i < methods.length - 1 ? '1px solid var(--border-color)' : 'none',
                    background: i % 2 === 0 ? 'transparent' : 'rgba(0,255,255,0.02)'
                }}>
                    {/* Method name bar */}
                    <div style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ padding: '5px 7px', background: 'rgba(234,179,8,0.1)', borderRadius: '7px', border: '1px solid rgba(234,179,8,0.2)', display: 'flex' }}>
                            <Zap size={13} color="#EAB308" />
                        </div>
                        <code style={{ fontSize: '0.92rem', fontWeight: '700', color: 'var(--text-primary)' }}>{m.name}()</code>
                        {m.isAsync && (
                            <span style={{ fontSize: '0.58rem', fontWeight: '900', padding: '2px 8px', borderRadius: '20px', background: 'rgba(168,85,247,0.15)', color: 'var(--accent-purple)', border: '1px solid rgba(168,85,247,0.3)', letterSpacing: '1.5px' }}>ASYNC</span>
                        )}
                    </div>
                    {/* Doc */}
                    <div style={{ padding: '0 20px 12px 20px' }}>
                        <p style={{ margin: 0, fontSize: '0.88rem', lineHeight: 1.7, opacity: 0.85 }}>{m.doc || 'System-level execution protocol.'}</p>
                    </div>
                    {/* Params + Returns footer */}
                    {(m.params?.length > 0 || m.returns) && (
                        <div style={{ padding: '10px 20px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '12px', background: 'var(--header-bg)' }}>
                            {m.params?.length > 0 && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '7px', flexWrap: 'wrap' }}>
                                    <span style={{ fontSize: '0.58rem', fontWeight: '900', color: '#EAB308', letterSpacing: '1.5px', opacity: 0.7 }}>PARAMS</span>
                                    {m.params.map((p, pi) => (
                                        <span key={pi} style={{ fontSize: '0.75rem', padding: '2px 10px', borderRadius: '20px', background: 'rgba(234,179,8,0.08)', color: '#EAB308', border: '1px solid rgba(234,179,8,0.2)', fontFamily: 'monospace' }}>{p}</span>
                                    ))}
                                </div>
                            )}
                            {m.returns && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginLeft: m.params?.length > 0 ? 'auto' : '0' }}>
                                    <span style={{ fontSize: '0.58rem', fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '1.5px', opacity: 0.7 }}>RETURNS</span>
                                    <span style={{ fontSize: '0.75rem', padding: '2px 10px', borderRadius: '20px', background: 'rgba(251,191,36,0.1)', color: 'var(--accent-ochre)', border: '1px solid rgba(251,191,36,0.25)', fontFamily: 'monospace' }}>{m.returns.length > 45 ? m.returns.slice(0, 45) + '…' : m.returns}</span>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            ))}
        </div>
    </SectionCard>
);


// ── Section: REFERENCE DOCS ───────────────────────────────────────────────────
const ReferenceDocsSection = ({ links }) => (
    <SectionCard accentColor="var(--accent-ochre)">
        <SectionHeader icon={BookOpen} title="REFERENCE DOCS" color="var(--accent-ochre)" />
        <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {links.length > 0 ? links.map((link, i) => (
                <a key={i} href={link.url} target="_blank" rel="noreferrer"
                    style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderRadius: '8px', background: 'var(--nav-hover-bg)', color: 'var(--accent-cyan)', textDecoration: 'none', fontSize: '0.88rem', fontWeight: '700', transition: 'background 0.15s', border: '1px solid var(--border-color)' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--nav-hover-bg-hover)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'var(--nav-hover-bg)'}
                >
                    <Globe size={13} color="var(--accent-cyan)" style={{ flexShrink: 0 }} />
                    {link.label}
                </a>
            )) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', borderRadius: '8px', background: 'var(--nav-hover-bg)', color: 'var(--accent-cyan)', fontSize: '0.88rem', fontWeight: '700', border: '1px solid var(--border-color)' }}>
                    <BookOpen size={16} /> NO VALID LINK PROVIDED
                </div>
            )}
        </div>
    </SectionCard>
);

// ── Section: MCP SERVERS IN USE ─────────────────────────────────────────────
const McpServersSection = ({ servers }) => (
    <SectionCard accentColor="var(--accent-purple)">
        <SectionHeader icon={Terminal} title="MCP SERVERS IN USE" color="var(--accent-purple)" />
        <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {servers.map((srv, i) => (
                <div key={i} style={{ background: 'var(--nav-hover-bg)', borderRadius: '10px', border: '1px solid var(--accent-purple)', overflow: 'hidden' }}>
                    {/* Server name header */}
                    <div style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--accent-purple-light)', borderBottom: '1px solid var(--accent-purple-border)' }}>
                        <Server size={14} color="var(--accent-purple)" />
                        <span style={{ fontSize: '0.85rem', fontWeight: '900', color: 'var(--accent-purple)' }}>{srv.name}</span>
                        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <div className={srv.status === 'Offline' ? '' : 'status-pulse'} style={{ width: '6px', height: '6px', borderRadius: '50%', background: srv.status === 'Offline' ? 'var(--accent-red)' : 'var(--accent-green)' }} />
                            <span style={{ fontSize: '0.6rem', fontWeight: '900', color: srv.status === 'Offline' ? 'var(--accent-red)' : 'var(--accent-green)' }}>{srv.status === 'Offline' ? 'OFFLINE' : 'ACTIVE'}</span>
                        </div>
                    </div>
                    {/* Fields */}
                    <div style={{ padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {srv.path && (
                            <div>
                                <span style={{ fontSize: '0.58rem', fontWeight: '900', color: 'var(--accent-green)', letterSpacing: '1.5px', opacity: 0.7, display: 'block', marginBottom: '4px' }}>INSTALLED PATH</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(34,197,94,0.08)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(34,197,94,0.2)' }}>
                                    <Cpu size={13} color="var(--accent-green)" />
                                    <code style={{ fontSize: '0.78rem', color: 'var(--accent-green)', fontWeight: '700' }}>{srv.path}</code>
                                </div>
                            </div>
                        )}
                        {srv.source_url && (
                            <a href={srv.source_url} target="_blank" rel="noreferrer"
                                style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', borderRadius: '8px', background: 'rgba(168,85,247,0.05)', color: 'var(--accent-cyan)', textDecoration: 'none', fontSize: '0.8rem', fontWeight: '700', border: '1px solid rgba(168,85,247,0.15)' }}
                            >
                                <Globe size={12} /> VIEW REPOSITORY
                            </a>
                        )}
                        {srv.env_vars?.length > 0 && (
                            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                <span style={{ fontSize: '0.58rem', fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '1.5px', opacity: 0.7, alignSelf: 'center' }}>ENV VARS</span>
                                {srv.env_vars.map((v, vi) => (
                                    <code key={vi} style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: '20px', background: 'rgba(234,179,8,0.08)', color: 'var(--accent-ochre)', border: '1px solid rgba(234,179,8,0.15)' }}>{v}</code>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    </SectionCard>
);

// ── Section: CODE TOOLS ───────────────────────────────────────────────────────
const CodeToolsSection = ({ tools: codeTools }) => (
    <SectionCard accentColor="#EAB308">
        <SectionHeader icon={Code} title="CODE TOOLS & LIBRARIES" color="#EAB308" />
        <div style={{ padding: '10px 16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {codeTools.map((ct, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 14px', background: 'var(--nav-hover-bg)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ padding: '4px 6px', background: 'var(--accent-ochre-light)', borderRadius: '6px' }}>
                        <Code size={12} color="#EAB308" />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <code style={{ fontSize: '0.85rem', fontWeight: '800', color: 'var(--text-primary)' }}>{ct.name}</code>
                            {ct.version && <span style={{ fontSize: '0.62rem', color: '#EAB308', opacity: 0.7, fontWeight: '700' }}>{ct.version}</span>}
                        </div>
                        {ct.purpose && <span style={{ fontSize: '0.75rem', opacity: 0.65 }}>{ct.purpose}</span>}
                    </div>
                </div>
            ))}
        </div>
    </SectionCard>
);

// ── Section: CONNECTION CONFIG (legacy flat for pure MCP servers) ─────────────
const ConnectionConfigSection = ({ tool }) => (
    <SectionCard accentColor="var(--accent-purple)">
        <SectionHeader icon={Terminal} title="CONNECTION CONFIG" color="var(--accent-purple)" />
        <div style={{ padding: '16px 22px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {tool.mcp_path && (
                <div style={{ marginBottom: '8px' }}>
                    <span style={{ fontSize: '0.6rem', fontWeight: '900', color: 'var(--accent-green)', letterSpacing: '1.5px', opacity: 0.8, display: 'block', marginBottom: '6px' }}>INSTALLED PATH</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(34,197,94,0.1)', padding: '12px 16px', borderRadius: '10px', border: '1px solid rgba(34,197,94,0.3)' }}>
                        <Cpu size={16} color="var(--accent-green)" />
                        <code style={{ fontSize: '0.82rem', fontWeight: '800', color: 'var(--accent-green)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{tool.mcp_path}</code>
                    </div>
                </div>
            )}
            {tool.mcp_source_url && (
                <a href={tool.mcp_source_url} target="_blank" rel="noreferrer"
                    style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', borderRadius: '8px', background: 'rgba(168,85,247,0.1)', color: 'var(--accent-cyan)', textDecoration: 'none', fontSize: '0.82rem', fontWeight: '900', border: '1px solid rgba(168,85,247,0.2)', justifyContent: 'center', letterSpacing: '0.5px' }}
                >
                    <Globe size={13} /> VIEW TOOL SOURCE / HOMEPAGE
                </a>
            )}
            {tool.mcp_env_vars?.map((v, i) => <CodeRow key={i} label={`ENV VAR ${i + 1}`} value={v} />)}
        </div>
    </SectionCard>
);

// ── Section: API QUICK-COMMANDS (Hybrid only) ─────────────────────────────────
const ApiCommandsSection = ({ calls }) => (
    <SectionCard accentColor="var(--accent-cyan)">
        <SectionHeader icon={Table2} title="API QUICK-COMMANDS" color="var(--accent-cyan)" />
        <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                <thead>
                    <tr style={{ background: 'var(--nav-hover-bg)' }}>
                        {['ACTION', 'ENDPOINT', 'NOTES'].map(h => (
                            <th key={h} style={{ padding: '8px 16px', textAlign: 'left', fontSize: '0.6rem', fontWeight: '900', color: 'var(--accent-cyan)', letterSpacing: '1.5px', opacity: 0.7, whiteSpace: 'nowrap' }}>{h}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {calls.map((c, i) => (
                        <tr key={i} style={{ borderTop: '1px solid var(--border-color)' }}>
                            <td style={{ padding: '10px 16px', fontWeight: '700', whiteSpace: 'nowrap', color: 'var(--text-primary)' }}>{c.action}</td>
                            <td style={{ padding: '10px 16px' }}><code style={{ background: 'rgba(0,255,255,0.08)', color: 'var(--accent-cyan)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>{c.endpoint}</code></td>
                            <td style={{ padding: '10px 16px', opacity: 0.7, lineHeight: 1.4 }}>{c.notes}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </SectionCard>
);


// ── Main component ─────────────────────────────────────────────────────────────
const ToolRegistry = () => {
    const [tools, setTools] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedTool, setSelectedTool] = useState(null);
    const [editorContent, setEditorContent] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [loadingSource, setLoadingSource] = useState(false);
    const [viewMode, setViewMode] = useState('visual');
    const [activeTab, setActiveTab] = useState('native'); // 'native' | 'mcp' | 'code'
    const [consultMessages, setConsultMessages] = useState([]);
    const [consultInput, setConsultInput] = useState('');
    const [isConsulting, setIsConsulting] = useState(false);
    const [isConsultOpen, setIsConsultOpen] = useState(false);

    const fetchTools = async () => {
        setLoading(true);
        try {
            const [skillsResp, mcpResp, codeResp] = await Promise.all([
                axios.get(`${API_BASE}/tools/registries/skills`),
                axios.get(`${API_BASE}/tools/registries/mcp`),
                axios.get(`${API_BASE}/tools/registries/code_tools`)
            ]);

            const getArray = (resp) => Array.isArray(resp.data?.data) ? resp.data.data : (Array.isArray(resp.data) ? resp.data : []);

            const skills = getArray(skillsResp).map(s => ({
                ...s,
                type: 'Skill',
                subtype: s.archetype || 'skill'
            }));

            const mcpServers = getArray(mcpResp).map(m => ({
                ...m,
                type: 'MCP Server',
                archetype: 'mcp',
                subtype: 'mcp',
                description: m.path ? `Local Server: ${m.path}` : 'External Server Connection',
                icon: 'server',
                mcp_path: m.path,
                mcp_source_url: m.source_url,
                mcp_env_vars: m.env_vars || []
            }));

            const codeTools = getArray(codeResp).map(c => ({
                ...c,
                type: 'Code Tool',
                archetype: 'code',
                subtype: 'code',
                description: c.purpose || `Version: ${c.version || 'latest'}`,
                icon: 'code'
            }));

            setTools([...skills, ...mcpServers, ...codeTools]);
        } catch (e) {
            console.error('Failed to fetch tool registries', e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchTools(); }, []);

    const openEditor = async (tool) => {
        setSelectedTool(tool);
        setViewMode('visual');
        setEditorContent('');
        if (!tool.filename) return;
        setLoadingSource(true);
        try {
            const resp = await axios.get(`${API_BASE}/tools/source?filename=${tool.filename}`);
            if (resp.data.status === 'success') setEditorContent(resp.data.content);
            else { alert('Error loading source: ' + resp.data.message); setSelectedTool(null); }
        } catch { alert('Network error loading source.'); setSelectedTool(null); }
        finally { setLoadingSource(false); }
    };

    const handleSaveSource = async () => {
        setIsSaving(true);
        try {
            const resp = await axios.post(`${API_BASE}/tools/source`, { filename: selectedTool.filename, content: editorContent });
            if (resp.data.status === 'success') alert('Tool Source Saved Successfully.');
            else alert('Error saving: ' + resp.data.message);
        } catch { alert('Network error saving source.'); }
        finally { setIsSaving(false); }
    };

    const handleConsult = async () => {
        if (!consultInput.trim() || !selectedTool) return;
        
        const userMsg = { role: 'user', content: consultInput };
        setConsultMessages(prev => [...prev, userMsg]);
        setConsultInput('');
        setIsConsulting(true);
        
        try {
            const resp = await axios.post(`${API_BASE}/registry/consult`, {
                tool_name: selectedTool.name,
                tool_type: selectedTool.type || 'Skill',
                tool_description: selectedTool.description,
                tool_source: editorContent,
                tool_metadata: {
                    archetype: selectedTool.archetype,
                    subtype: selectedTool.subtype,
                    mcp_path: selectedTool.mcp_path,
                    docs_links: selectedTool.docs_links
                },
                messages: [...consultMessages, userMsg]
            });
            
            if (resp.data.status === 'success') {
                setConsultMessages(prev => [...prev, { role: 'assistant', content: resp.data.response }]);
            }
        } catch (e) {
            setConsultMessages(prev => [...prev, { role: 'system', content: 'Connection to Guide Consult failed.' }]);
        }
        setIsConsulting(false);
    };

    const ContextConsultPanel = () => (
        <div style={{ 
            marginTop: '20px', 
            border: '1px solid var(--border-color)', 
            borderRadius: '16px', 
            overflow: 'hidden',
            background: 'var(--header-bg)',
            display: 'flex',
            flexDirection: 'column',
            maxHeight: isConsultOpen ? '400px' : '48px',
            transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: isConsultOpen ? '0 10px 25px -5px rgba(0,0,0,0.3)' : 'none'
        }}>
            <div 
                onClick={() => setIsConsultOpen(!isConsultOpen)}
                style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', background: 'var(--nav-hover-bg)' }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Activity size={16} color="var(--accent-cyan)" />
                    <span style={{ fontSize: '0.75rem', fontWeight: '900', letterSpacing: '1px' }}>GUIDE CONTEXTUAL CONSULT</span>
                </div>
                {isConsultOpen ? <X size={16} /> : <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {consultMessages.length > 0 && <span style={{ fontSize: '0.65rem', padding: '2px 8px', borderRadius: '10px', background: 'var(--accent-cyan)', color: 'black', fontWeight: '900' }}>{consultMessages.length}</span>}
                    <Zap size={14} className="status-pulse" color="var(--accent-cyan)" />
                </div>}
            </div>

            {isConsultOpen && (
                <div style={{ display: 'flex', flexDirection: 'column', height: '352px' }}>
                    <div style={{ flex: 1, overflowY: 'auto', padding: '15px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {consultMessages.length === 0 && (
                            <div style={{ textAlign: 'center', marginTop: '40px', padding: '0 20px' }}>
                                <Brain size={32} color="var(--accent-cyan)" style={{ marginBottom: '12px', opacity: 0.3 }} />
                                <p style={{ fontSize: '0.8rem', opacity: 0.6 }}>
                                    Ask Guide anything about this {selectedTool.type || 'tool'}.<br/>
                                </p>
                                <span style={{ fontSize: '0.7rem', opacity: 0.4 }}>"How do I use this?" or "Suggest an update..."</span>
                            </div>
                        )}
                        {consultMessages.map((m, i) => (
                            <div key={i} style={{ 
                                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                                maxWidth: '85%',
                                padding: '10px 14px',
                                borderRadius: '12px',
                                background: m.role === 'user' ? 'var(--accent-cyan)' : 'var(--panel-bg)',
                                color: m.role === 'user' ? 'black' : 'var(--text-primary)',
                                fontSize: '0.82rem',
                                border: m.role === 'assistant' ? '1px solid var(--border-color)' : 'none',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                            }}>
                                {m.content}
                            </div>
                        ))}
                        {isConsulting && (
                            <div style={{ alignSelf: 'flex-start', padding: '10px 14px', borderRadius: '12px', background: 'var(--panel-bg)', border: '1px solid var(--border-color)' }}>
                                <RefreshCw className="spin" size={14} />
                            </div>
                        )}
                    </div>
                    
                    <div style={{ padding: '12px', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '10px', background: 'var(--panel-bg)' }}>
                        <input 
                            value={consultInput}
                            onChange={e => setConsultInput(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleConsult()}
                            placeholder="Consult Guide..."
                            style={{ flex: 1, background: 'var(--bg-color)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '8px 12px', fontSize: '0.8rem', color: 'var(--text-primary)' }}
                        />
                        <button onClick={handleConsult} disabled={isConsulting} className="button-primary" style={{ padding: '8px' }}>
                            <Play size={16} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );

    const getIcon = (iconName) => {
        const icons = { browser: Globe, docker: Monitor, file: FileText, mail: Mail, drive: Database, workflow: Cpu, office: FileText, activity: Play, database: Database, eye: Eye, mic: Mic, speaker: Speaker, globe: Globe, brain: Brain, folder: Folder, code: Code };
        const subtypeColors = { mcp: 'var(--accent-purple)', hybrid: 'var(--accent-ochre)', skill: 'var(--accent-cyan)' };
        const Icon = icons[iconName] || Wrench;
        return <Icon size={24} color="var(--accent-cyan)" />;
    };

    // ── Registry grid card ─────────────────────────────────────────────────────
    const subtypeBorder = (t) => {
        if (t.subtype === 'mcp') return 'var(--accent-purple)';
        if (t.subtype === 'hybrid') return 'var(--accent-ochre)';
        return 'var(--accent-cyan)';
    };
    const subtypeLabel = (t) => {
        if (t.subtype === 'hybrid') return 'HYBRID';
        if (t.subtype === 'mcp') return 'MCP';
        if (t.type === 'Code Tool') return 'CODE TOOL';
        return 'NATIVE SKILL';
    };

    const ToolCard = ({ tool }) => {
        if (!tool) return null;
        const border = subtypeBorder(tool);
        return (
            <motion.div layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className="card" onClick={() => openEditor(tool)}
                style={{ padding: '24px', borderTop: `3px solid ${border}`, background: 'var(--panel-bg)', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '100%', minHeight: '200px', boxShadow: 'var(--card-shadow)', cursor: 'pointer' }}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                        <div style={{ padding: '11px', borderRadius: '11px', background: `${border}18`, border: `1px solid ${border}` }}>
                            {getIcon(tool?.icon)}
                        </div>
                        <div>
                            <h3 style={{ fontSize: '0.95rem', fontWeight: '800', margin: 0 }}>{tool?.name || 'Unknown Tool'}</h3>
                            <span 
                                title={HELP_DATA[subtypeLabel(tool)] || ''}
                                style={{ 
                                    fontSize: '0.6rem', 
                                    color: border, 
                                    fontWeight: '900', 
                                    textTransform: 'uppercase', 
                                    letterSpacing: '1.5px',
                                    cursor: 'help',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '4px'
                                }}
                            >
                                {subtypeLabel(tool)}
                                <HelpCircle size={10} style={{ opacity: 0.5 }} />
                            </span>
                        </div>
                    </div>
                </div>

                {tool.type === 'MCP Server' && tool.status && (
                    <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <div className={tool.status === 'Offline' ? '' : 'status-pulse'} style={{ width: '6px', height: '6px', borderRadius: '50%', background: tool.status === 'Offline' ? 'var(--accent-red)' : 'var(--accent-green)' }} />
                        <span style={{ fontSize: '0.65rem', fontWeight: '900', color: tool.status === 'Offline' ? 'var(--accent-red)' : 'var(--accent-green)', letterSpacing: '1.5px' }}>
                            {tool.status.toUpperCase()}
                        </span>
                    </div>
                )}

                <p style={{ fontSize: '0.83rem', opacity: 0.8, flex: 1, lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '14px' }}>
                    {tool?.description || 'No description provided.'}
                </p>
                <div style={{ marginTop: 'auto', paddingTop: '13px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                        <div className="status-pulse" style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--accent-green)' }} />
                        <span style={{ fontSize: '0.65rem', fontWeight: '800', color: 'var(--text-primary)' }}>{(tool?.status || 'Unknown').toUpperCase()}</span>
                    </div>
                    {tool.docs_links?.length > 0 && (
                        <span style={{ fontSize: '0.6rem', color: 'var(--accent-ochre)', fontWeight: '700', opacity: 0.8 }}>📚 {tool.docs_links.length} DOCS</span>
                    )}
                </div>
            </motion.div>
        );
    };

    // ── Visual Map renderer (data-driven) ──────────────────────────────────────
    const renderVisualMap = () => {
        if (loadingSource) return <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.5 }}>LOADING SOURCE...</div>;

        const isCodeTool = selectedTool?.type === 'Code Tool';
        const archetype = selectedTool?.archetype || selectedTool?.subtype || 'skill';
        const hasSource = !!selectedTool?.filename;

        // Parse source for skills with python files
        const parsed = (archetype === 'mcp' || isCodeTool)
            ? { classDesc: selectedTool?.description || 'No description.', methods: [] }
            : parsePythonScript(editorContent, selectedTool?.description);

        const hasMethods = parsed.methods.length > 0 && archetype !== 'mcp' && !isCodeTool;
        const hasDocs = (selectedTool?.docs_links?.length || 0) > 0;
        const hasMcpServers = (selectedTool?.mcp_servers?.length || 0) > 0;
        const hasCodeTools = (selectedTool?.code_tools?.length || 0) > 0;
        // For pure MCP server registry entries, use legacy flat fields
        const useLegacyMcp = archetype === 'mcp' && !hasMcpServers;
        const hasApiCalls = (selectedTool?.sample_calls?.length || 0) > 0;

        return (
            <div style={{ 
                flex: 1, 
                overflowY: 'auto', 
                padding: '20px', 
                display: 'grid', 
                gridTemplateColumns: 'repeat(12, 1fr)', 
                gridAutoRows: 'min-content',
                gap: '20px' 
            }}>
                {/* 1: Overview (Thinking) — Hero Block */}
                <div style={{ gridColumn: 'span 8' }}>
                    <OverviewSection tool={selectedTool} classDesc={parsed.classDesc} />
                </div>

                {/* 5: Reference Docs (Read) — Side Block */}
                <div style={{ gridColumn: 'span 4' }}>
                    {hasDocs ? <ReferenceDocsSection links={selectedTool.docs_links} /> : (
                        <SectionCard accentColor="var(--accent-ochre)">
                            <SectionHeader icon={BookOpen} title="REFERENCE DOCS" color="var(--accent-ochre)" />
                            <div style={{ padding: '20px', textAlign: 'center', opacity: 0.4, fontSize: '0.85rem', fontStyle: 'italic' }}>NONE DEFINED</div>
                        </SectionCard>
                    )}
                </div>

                {/* 2: Execution Nodes — Large block */}
                <div style={{ gridColumn: 'span 8', gridRow: 'span 2' }}>
                    {archetype !== 'mcp' && !isCodeTool ? (
                        hasMethods ? <ExecutionNodesSection methods={parsed.methods} /> : (
                            <SectionCard accentColor="var(--accent-ochre)" style={{ height: '100%' }}>
                                <SectionHeader icon={Zap} title="EXECUTION NODES" color="var(--accent-ochre)" />
                                <div style={{ padding: '40px', textAlign: 'center', opacity: 0.4, fontSize: '0.85rem', fontStyle: 'italic' }}>NONE DEFINED</div>
                            </SectionCard>
                        )
                    ) : (
                        <SectionCard accentColor="var(--accent-ochre)" style={{ height: '100%' }}>
                            <SectionHeader icon={Zap} title="EXECUTION NODES" color="var(--accent-ochre)" />
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem', fontStyle: 'italic' }}>NONE (HANDLED VIA MCP PROTOCOL)</div>
                        </SectionCard>
                    )}
                </div>

                {/* 3a: MCP Servers In Use (Skills with MCP) */}
                <div style={{ gridColumn: 'span 4' }}>
                    {hasMcpServers ? (
                        <McpServersSection servers={selectedTool.mcp_servers} />
                    ) : useLegacyMcp ? (
                        <ConnectionConfigSection tool={selectedTool} />
                    ) : (
                        <SectionCard accentColor="var(--accent-purple)">
                            <SectionHeader icon={Terminal} title="MCP SERVERS IN USE" color="var(--accent-purple)" />
                            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem', fontStyle: 'italic' }}>NONE DEFINED</div>
                        </SectionCard>
                    )}
                </div>

                {/* 3b: Code Tools & Libraries */}
                <div style={{ gridColumn: 'span 4' }}>
                    {hasCodeTools ? (
                        <CodeToolsSection tools={selectedTool.code_tools} />
                    ) : (
                        <SectionCard accentColor="#EAB308">
                            <SectionHeader icon={Code} title="CODE TOOLS & LIBRARIES" color="#EAB308" />
                            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem', fontStyle: 'italic' }}>NONE DEFINED</div>
                        </SectionCard>
                    )}
                </div>

                {/* Code Tool info footer if needed */}
                {isCodeTool && (
                    <div style={{ gridColumn: 'span 12' }}>
                        <SectionCard accentColor="var(--accent-cyan)">
                            <SectionHeader icon={Code} title="CODE TOOL" color="var(--accent-cyan)" />
                            <div style={{ padding: '16px 22px' }}>
                                <p style={{ margin: 0, opacity: 0.85, fontSize: '0.9rem', lineHeight: 1.7 }}>
                                    Dynamically generated Code Tool. Raw execution code stored in{' '}
                                    <code style={{ background: 'var(--nav-hover-bg)', padding: '1px 6px', borderRadius: '4px', fontSize: '0.78rem' }}>gemini_workspace/canvas_artifacts</code>.
                                    Only its interface is exposed to the agent swarm.
                                </p>
                            </div>
                        </SectionCard>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '24px', overflow: 'hidden', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--accent-ochre)', margin: 0, display: 'flex', alignItems: 'center', gap: '14px' }}>
                        <Puzzle size={30} /> TOOL & SKILL REGISTRY
                    </h2>
                    <p style={{ opacity: 0.6, fontSize: '0.88rem', marginTop: '5px' }}>Platform capabilities, MCP integrations, and hybrid automations.</p>
                </div>
                <button onClick={fetchTools} className="button-secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <RefreshCw size={16} className={loading ? 'spin' : ''} /> REFRESH REGISTRY
                </button>
            </div>

            {/* Navigation Tabs */}
            <div style={{ display: 'flex', gap: '8px', background: 'var(--header-bg)', padding: '6px', borderRadius: '12px', width: 'fit-content' }}>
                {[
                    { id: 'native', label: 'SKILLS', icon: Puzzle },
                    { id: 'mcp', label: 'MCP SERVERS', icon: Server },
                    { id: 'code', label: 'CODE TOOLS', icon: Code }
                ].map(tab => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button 
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            style={{ 
                                display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 20px', 
                                borderRadius: '8px', border: 'none', cursor: 'pointer', fontSize: '0.75rem', 
                                fontWeight: '900', letterSpacing: '1px', transition: 'all 0.2s',
                                background: isActive ? 'var(--accent-ochre)' : 'transparent',
                                color: isActive ? 'var(--overlay-heavy-bg)' : 'var(--text-primary)',
                                boxShadow: isActive ? '0 4px 12px rgba(251,191,36,0.2)' : 'none'
                            }}
                        >
                            <Icon size={16} />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {loading ? (
                <div style={{ padding: '40px', textAlign: 'center', opacity: 0.5, flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>SCANNING REGISTRY...</div>
            ) : (
                <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gridAutoRows: '220px', gap: '22px', overflowY: 'auto', paddingRight: '5px' }}>
                    
                    {/* MCP Discovery Portal CTA */}
                    {activeTab === 'mcp' && (
                        <motion.div 
                            whileHover={{ scale: 1.02 }}
                            onClick={() => window.location.href = '/forge'} // Link to SkillForge for now
                            style={{ 
                                padding: '24px', border: '2px dashed var(--accent-cyan)', background: 'rgba(0,255,255,0.03)', 
                                borderRadius: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', 
                                justifyContent: 'center', gap: '14px', cursor: 'pointer', textAlign: 'center'
                            }}
                        >
                            <div style={{ padding: '12px', background: 'rgba(0,255,255,0.1)', borderRadius: '50%' }}>
                                <RefreshCw size={24} color="var(--accent-cyan)" />
                            </div>
                            <div>
                                <h3 style={{ fontSize: '0.9rem', fontWeight: '900', color: 'var(--accent-cyan)', margin: 0 }}>DISCOVER NEW MCP</h3>
                                <p style={{ fontSize: '0.72rem', opacity: 0.6, marginTop: '4px' }}>Deep Recon → GitHub Search → Skill Mapping</p>
                            </div>
                        </motion.div>
                    )}

                    <AnimatePresence>
                        {tools
                            .filter(tool => {
                                const type = (tool.type || '');
                                if (activeTab === 'code') return type === 'Code Tool';
                                if (activeTab === 'mcp') return type === 'MCP Server';
                                // Skills tab: all Skill entries (archetype skill, hybrid, etc.)
                                return type === 'Skill';
                            })
                            .map((tool, idx) => <ToolCard key={tool.name + idx} tool={tool} />)}
                    </AnimatePresence>
                </div>
            )}

            {/* Drill-Down Overlay */}
            <AnimatePresence>
                {selectedTool && (
                    <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }}
                        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'var(--bg-color)', zIndex: 100, display: 'flex', flexDirection: 'column', padding: '20px' }}
                    >
                        {/* Overlay header */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                                <Code size={22} color={subtypeBorder(selectedTool)} />
                                <div>
                                    <h2 style={{ fontSize: '1.3rem', margin: 0, fontWeight: '900' }}>{selectedTool?.name}</h2>
                                    <span style={{ fontSize: '0.72rem', opacity: 0.5 }}>{selectedTool?.filename || selectedTool?.type}</span>
                                </div>
                                <span 
                                    title={HELP_DATA[subtypeLabel(selectedTool)] || ''}
                                    style={{ fontSize: '0.62rem', fontWeight: '900', padding: '3px 10px', borderRadius: '20px', background: `${subtypeBorder(selectedTool)}22`, color: subtypeBorder(selectedTool), border: `1px solid ${subtypeBorder(selectedTool)}55`, letterSpacing: '1px', cursor: 'help', display: 'flex', alignItems: 'center', gap: '4px' }}
                                >
                                    {subtypeLabel(selectedTool)}
                                    <HelpCircle size={10} style={{ opacity: 0.5 }} />
                                </span>
                            </div>
                            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                {/* View toggle */}
                                <div style={{ display: 'flex', background: 'var(--header-bg)', borderRadius: '8px', padding: '4px' }}>
                                    {['visual', 'code'].map(m => (
                                        <button key={m} onClick={() => setViewMode(m)}
                                            disabled={m === 'code' && !selectedTool?.filename}
                                            style={{ padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: m === 'code' && !selectedTool?.filename ? 'not-allowed' : 'pointer', fontSize: '0.75rem', fontWeight: '900', opacity: m === 'code' && !selectedTool?.filename ? 0.4 : 1, background: viewMode === m ? 'var(--accent-ochre)' : 'transparent', color: viewMode === m ? 'var(--overlay-heavy-bg)' : 'var(--text-primary)' }}
                                        >{m === 'visual' ? 'VISUAL MAP' : 'RAW CODE'}</button>
                                    ))}
                                </div>
                                <button className="button-primary" onClick={handleSaveSource}
                                    disabled={isSaving || loadingSource || !selectedTool?.filename}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: selectedTool?.filename ? 1 : 0.4 }}
                                >
                                    {isSaving ? <RefreshCw className="spin" size={15} /> : <Save size={15} />} SAVE
                                </button>
                                <button className="button-secondary" onClick={() => setSelectedTool(null)}><X size={17} /></button>
                            </div>
                        </div>
                        {/* TL;DR Insight Rail */}
                        <div className="glass-panel" style={{ 
                            display: 'flex', gap: '24px', padding: '12px 24px', background: 'var(--panel-bg)', 
                            borderRadius: '16px', border: '1px solid var(--border-color)', marginBottom: '20px',
                            alignItems: 'center', flexShrink: 0
                        }}>
                             <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '0.65rem', fontWeight: '900', opacity: 0.4 }}>TYPE:</span>
                                <span style={{ fontSize: '0.8rem', fontWeight: '800', color: subtypeBorder(selectedTool) }}>{subtypeLabel(selectedTool)}</span>
                             </div>
                             <div style={{ width: '1px', height: '20px', background: 'var(--border-color)' }} />
                             <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '0.65rem', fontWeight: '900', opacity: 0.4 }}>STATUS:</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <div className="status-pulse" style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-green)' }} />
                                    <span style={{ fontSize: '0.8rem', fontWeight: '800' }}>CONNECTED</span>
                                </div>
                             </div>
                             <div style={{ width: '1px', height: '20px', background: 'var(--border-color)' }} />
                             <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '0.65rem', fontWeight: '900', opacity: 0.4 }}>NODES:</span>
                                <span style={{ fontSize: '0.8rem', fontWeight: '800', color: '#EAB308' }}>
                                    {(selectedTool.subtype === 'mcp' || selectedTool.type === 'Code Tool') ? 'DYNAMIC' : `${parsePythonScript(editorContent).methods.length}`}
                                </span>
                             </div>
                             {selectedTool.mcp_path && (
                                <>
                                    <div style={{ width: '1px', height: '20px', background: 'var(--border-color)' }} />
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', maxWidth: '300px' }}>
                                        <span style={{ fontSize: '0.65rem', fontWeight: '900', opacity: 0.4 }}>PATH:</span>
                                        <code style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--accent-green)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{selectedTool.mcp_path}</code>
                                    </div>
                                </>
                             )}
                        </div>

                        {viewMode === 'visual' ? renderVisualMap() : (
                            <textarea value={editorContent} onChange={e => setEditorContent(e.target.value)} spellCheck="false"
                                style={{ flex: 1, width: '100%', padding: '20px', borderRadius: '12px', border: '1px solid var(--border-color)', background: 'var(--panel-bg)', color: 'var(--text-primary)', fontFamily: 'monospace', fontSize: '0.82rem', lineHeight: 1.6, resize: 'none', boxSizing: 'border-box' }}
                             />
                        )}

                        <ContextConsultPanel />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default ToolRegistry;
