import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Puzzle, Globe, Database, Monitor, FileText, Cpu, Eye, Mic, Speaker, Brain, Play, Mail, Server, Wrench, RefreshCw, Folder, Code, Save, X, Activity, Zap } from 'lucide-react';
import { API_BASE } from '../api.js';

const ToolRegistry = () => {
    const [tools, setTools] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Editor State
    const [selectedTool, setSelectedTool] = useState(null);
    const [editorContent, setEditorContent] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [loadingSource, setLoadingSource] = useState(false);
    const [viewMode, setViewMode] = useState('visual'); // 'visual' | 'code'

    const fetchTools = async () => {
        setLoading(true);
        try {
            const resp = await axios.get(`${API_BASE}/tools/registry`);
            setTools(resp.data);
        } catch (e) {
            console.error("Failed to fetch tool registry", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTools();
    }, []);

    const openEditor = async (tool) => {
        setSelectedTool(tool);
        setViewMode('visual');
        setEditorContent('');
        
        if (!tool.filename) {
            // MCP tools don't have source code in this context
            return;
        }
        
        setLoadingSource(true);
        try {
            const resp = await axios.get(`${API_BASE}/tools/source?filename=${tool.filename}`);
            if (resp.data.status === 'success') {
                setEditorContent(resp.data.content);
            } else {
                alert("Error loading source: " + resp.data.message);
                setSelectedTool(null);
            }
        } catch (e) {
            alert("Network error loading source.");
            setSelectedTool(null);
        } finally {
            setLoadingSource(false);
        }
    };

    const parsePythonScript = (code, fallbackDesc) => {
        const lines = (code || '').split('\n');
        
        let classDesc = typeof fallbackDesc === 'string' ? fallbackDesc : 'Native Implementation Module.';
        const methods = [];
        
        let currentMethod = null;
        let inMethodDocstring = false;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();
            
            const defMatch = line.match(/^\s*(?:async\s+)?def ([a-zA-Z0-9_]+)\(/);
            if (defMatch) {
                if (currentMethod) methods.push(currentMethod);
                if (!defMatch[1].startsWith('_')) {
                    currentMethod = { name: defMatch[1], doc: '' };
                    inMethodDocstring = false;
                } else {
                    currentMethod = null;
                }
            } else if (currentMethod && trimmed.startsWith('"""')) {
                inMethodDocstring = !inMethodDocstring;
                currentMethod.doc = trimmed.replace(/"""/g, '');
            } else if (inMethodDocstring) {
                if (trimmed.startsWith('"""')) {
                    inMethodDocstring = false;
                } else {
                    currentMethod.doc += ' ' + trimmed;
                }
            }
        }
        if (currentMethod) methods.push(currentMethod);
        
        // Clean up excessive spaces safely
        if (classDesc && typeof classDesc === 'string') {
            classDesc = classDesc.replace(/\s+/g, ' ').trim();
        }
        methods.forEach(m => {
            if (m.doc && typeof m.doc === 'string') {
                m.doc = m.doc.replace(/\s+/g, ' ').trim();
            }
        });
        
        return { classDesc, methods };
    };

    const handleSaveSource = async () => {
        setIsSaving(true);
        try {
            const resp = await axios.post(`${API_BASE}/tools/source`, {
                filename: selectedTool.filename,
                content: editorContent
            });
            if (resp.data.status === 'success') {
                alert("Tool Source Saved Successfully.");
            } else {
                alert("Error saving: " + resp.data.message);
            }
        } catch (e) {
            alert("Network error saving source.");
        } finally {
            setIsSaving(false);
        }
    };

    const getIcon = (iconName) => {
        switch (iconName) {
            case 'browser': return <Globe size={24} color="var(--accent-cyan)" />;
            case 'docker': return <Monitor size={24} color="var(--accent-cyan)" />;
            case 'file': return <FileText size={24} color="var(--accent-cyan)" />;
            case 'mail': return <Mail size={24} color="var(--accent-cyan)" />;
            case 'drive': return <Database size={24} color="var(--accent-cyan)" />;
            case 'workflow': return <Cpu size={24} color="var(--accent-cyan)" />;
            case 'office': return <FileText size={24} color="var(--accent-cyan)" />;
            case 'activity': return <Play size={24} color="var(--accent-cyan)" />;
            case 'database': return <Database size={24} color="var(--accent-cyan)" />;
            case 'eye': return <Eye size={24} color="var(--accent-cyan)" />;
            case 'mic': return <Mic size={24} color="var(--accent-cyan)" />;
            case 'speaker': return <Speaker size={24} color="var(--accent-cyan)" />;
            case 'globe': return <Globe size={24} color="var(--accent-cyan)" />;
            case 'brain': return <Brain size={24} color="var(--accent-purple)" />;
            case 'folder': return <Folder size={24} color="var(--accent-purple)" />;
            default: return <Wrench size={24} color="var(--accent-cyan)" />;
        }
    };

    const ToolCard = ({ tool }) => {
        if (!tool) return null;
        const isMCP = tool?.type === 'MCP Server';
        const borderColor = isMCP ? 'var(--accent-purple)' : 'var(--accent-cyan)';
        
        return (
            <motion.div 
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="card" 
                onClick={() => openEditor(tool)}
                style={{ 
                    padding: '24px', 
                    borderTop: `3px solid ${borderColor}`,
                    background: 'var(--panel-bg)',
                    position: 'relative',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                    minHeight: '200px',
                    boxShadow: 'var(--card-shadow)',
                    cursor: 'pointer'
                }}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                        <div style={{ 
                            padding: '12px', 
                            borderRadius: '12px', 
                            background: isMCP ? 'rgba(168, 85, 247, 0.1)' : 'rgba(0, 255, 255, 0.1)',
                            border: `1px solid ${borderColor}`
                        }}>
                             {getIcon(tool?.icon)}
                        </div>
                        <div>
                            <h3 style={{ fontSize: '1rem', fontWeight: '800', margin: 0 }}>{tool?.name || 'Unknown Tool'}</h3>
                            <span style={{ fontSize: '0.65rem', color: borderColor, fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px' }}>
                                {tool?.type || 'Native Skill'}
                            </span>
                        </div>
                    </div>
                </div>

                <p style={{ 
                    fontSize: '0.85rem', 
                    opacity: 0.8, 
                    flex: 1, 
                    lineHeight: '1.5',
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    marginBottom: '15px'
                }}>
                    {tool?.description || 'No description provided.'}
                </p>

                <div style={{ marginTop: 'auto', paddingTop: '15px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div className="status-pulse" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-green)' }}></div>
                        <span style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-primary)' }}>{(tool?.status || 'Unknown').toUpperCase()}</span>
                    </div>
                </div>
            </motion.div>
        );
    };

    return (
        <div style={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '24px',
            overflow: 'hidden',
            padding: '20px'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--accent-ochre)', margin: 0, display: 'flex', alignItems: 'center', gap: '15px' }}>
                        <Puzzle size={30} />
                        TOOL & SKILL REGISTRY
                    </h2>
                    <p style={{ opacity: 0.6, fontSize: '0.9rem', marginTop: '5px' }}>Active platform capabilities and connected MCP integrations.</p>
                </div>
                <button onClick={fetchTools} className="button-secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <RefreshCw size={16} className={loading ? "spin" : ""} /> REFRESH REGISTRY
                </button>
            </div>

            {loading ? (
                <div style={{ padding: '40px', textAlign: 'center', opacity: 0.5, flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    SCANNING REGISTRY...
                </div>
            ) : (
                <div style={{ 
                    flex: 1, 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', 
                    gridAutoRows: '220px',
                    gap: '24px',
                    overflowY: 'auto',
                    paddingRight: '5px'
                }}>
                    <AnimatePresence>
                        {tools.map((tool, idx) => (
                            <ToolCard key={tool.name + idx} tool={tool} />
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Drill-Down Editor Overlay */}
            <AnimatePresence>
                {selectedTool && (
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            background: 'var(--bg-color)',
                            zIndex: 100,
                            display: 'flex',
                            flexDirection: 'column',
                            padding: '20px'
                        }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                                <Code size={24} color="var(--accent-cyan)" />
                                <div>
                                    <h2 style={{ fontSize: '1.4rem', margin: 0, fontWeight: '800' }}>{selectedTool?.name}</h2>
                                    <span style={{ fontSize: '0.8rem', opacity: 0.6 }}>{selectedTool?.filename}</span>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                {/* ADHD Mode Toggle */}
                                <div style={{ display: 'flex', background: 'var(--header-bg)', borderRadius: '8px', padding: '4px' }}>
                                    <button 
                                        onClick={() => setViewMode('visual')}
                                        style={{ 
                                            padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                                            fontSize: '0.8rem', fontWeight: '800',
                                            background: viewMode === 'visual' ? 'var(--accent-ochre)' : 'transparent',
                                            color: viewMode === 'visual' ? 'var(--overlay-heavy-bg)' : 'var(--text-primary)'
                                        }}
                                    >VISUAL MAP</button>
                                    <button 
                                        onClick={() => setViewMode('code')}
                                        disabled={!selectedTool?.filename}
                                        style={{ 
                                            padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: selectedTool?.filename ? 'pointer' : 'not-allowed',
                                            fontSize: '0.8rem', fontWeight: '800', opacity: selectedTool?.filename ? 1 : 0.4,
                                            background: viewMode === 'code' ? 'var(--accent-ochre)' : 'transparent',
                                            color: viewMode === 'code' ? 'var(--overlay-heavy-bg)' : 'var(--text-primary)'
                                        }}
                                    >RAW CODE</button>
                                </div>
                                <button 
                                    className="button-primary" 
                                    onClick={handleSaveSource}
                                    disabled={isSaving || loadingSource || !selectedTool?.filename}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: selectedTool?.filename ? 1 : 0.4 }}
                                >
                                    {isSaving ? <RefreshCw className="spin" size={16} /> : <Save size={16} />}
                                    SAVE SOURCE
                                </button>
                                <button className="button-secondary" onClick={() => setSelectedTool(null)}>
                                    <X size={18} />
                                </button>
                            </div>
                        </div>

                        {loadingSource ? (
                            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.5 }}>
                                LOADING SOURCE...
                            </div>
                        ) : viewMode === 'visual' ? (
                            // ADHD-Friendly Visual Presentation
                            (() => {
                                const isMCP = selectedTool?.type === 'MCP Server';
                                const isCodeTool = selectedTool?.type === 'Code Tool';
                                const parsed = (isMCP || isCodeTool) ? { classDesc: selectedTool?.description || 'No Description Available', methods: [] } : parsePythonScript(editorContent, selectedTool?.description);
                                
                                return (
                                    <div style={{ flex: 1, overflowY: 'auto', padding: '10px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                        <div className="card" style={{ padding: '24px', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', borderRadius: '12px' }}>
                                            <h3 style={{ margin: '0 0 10px 0', fontSize: '1.2rem', color: isMCP ? 'var(--accent-purple)' : 'var(--accent-cyan)' }}>Capability Overview</h3>
                                            <p style={{ lineHeight: '1.6', opacity: 0.9, fontSize: '0.95rem' }}>{parsed.classDesc}</p>
                                            
                                            {(selectedTool?.name || '').toLowerCase().includes('n8n') && (
                                                <div style={{ marginTop: '15px', padding: '15px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', borderLeft: '4px solid var(--accent-ochre)'}}>
                                                    <h4 style={{ margin: '0 0 10px 0', color: 'var(--accent-ochre)', fontSize: '1.05rem' }}>Reference Material</h4>
                                                    <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '1rem', opacity: 0.9, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                                        <li><a href="https://docs.n8n.io/api/" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-cyan)', textDecoration: 'none', fontWeight: 'bold' }}>n8n Public API Documentation</a></li>
                                                        <li><a href="https://github.com/n8n-io/n8n" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-cyan)', textDecoration: 'none', fontWeight: 'bold' }}>n8n Open Source Repository</a></li>
                                                        <li><a href="https://docs.n8n.io/integrations/" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-cyan)', textDecoration: 'none', fontWeight: 'bold' }}>n8n Nodes & Integrations Reference</a></li>
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                        
                                        {!isMCP && !isCodeTool && parsed.methods.length > 0 && (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                                                <h3 style={{ margin: '10px 0 0 0', fontSize: '1.1rem', color: 'var(--accent-ochre)' }}>Execution Nodes</h3>
                                                {parsed.methods.map((m, i) => (
                                                    <div key={i} className="card" style={{ padding: '16px 20px', background: 'var(--header-bg)', borderLeft: '4px solid var(--accent-cyan)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                            <div style={{ padding: '6px', background: 'rgba(0, 255, 255, 0.1)', borderRadius: '8px' }}>
                                                                <Zap size={16} color="var(--accent-cyan)" />
                                                            </div>
                                                            <strong style={{ fontSize: '1.05rem', letterSpacing: '0.5px' }}>{m.name}</strong>
                                                        </div>
                                                        <p style={{ margin: 0, fontSize: '0.9rem', opacity: 0.75, lineHeight: '1.5', paddingLeft: '36px' }}>{m.doc || 'System-level execution protocol.'}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                        
                                        {isMCP && (
                                             <div className="card" style={{ padding: '24px', background: 'rgba(168, 85, 247, 0.05)', border: '1px solid var(--accent-purple)' }}>
                                                 <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                                                    <Globe size={20} color="var(--accent-purple)" />
                                                    <h3 style={{ margin: 0, color: 'var(--accent-purple)' }}>MCP Integration Strategy</h3>
                                                 </div>
                                                 <p style={{ margin: 0, opacity: 0.8, fontSize: '0.9rem', lineHeight: '1.6' }}>This tool operates as an external Model Context Protocol server. Its internal architecture, execution nodes, and implementation details are abstracted away from this registry and handled by the remote server directly.</p>
                                             </div>
                                        )}

                                        {isCodeTool && (
                                             <div className="card" style={{ padding: '24px', background: 'rgba(0, 255, 255, 0.05)', border: '1px solid var(--accent-cyan)' }}>
                                                 <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                                                    <Code size={20} color="var(--accent-cyan)" />
                                                    <h3 style={{ margin: 0, color: 'var(--accent-cyan)' }}>Code Tool Strategy</h3>
                                                 </div>
                                                 <p style={{ margin: 0, opacity: 0.8, fontSize: '0.9rem', lineHeight: '1.6' }}>This is a dynamically generated Code Tool. Its raw execution code is safely stored within the standard `gemini_workspace/canvas_artifacts` schema. Only its interface and capability are exposed to the agent swarm for execution.</p>
                                             </div>
                                        )}
                                    </div>
                                );
                            })()
                        ) : (
                            <textarea 
                                value={editorContent}
                                onChange={(e) => setEditorContent(e.target.value)}
                                spellCheck="false"
                                style={{
                                    flex: 1,
                                    width: '100%',
                                    padding: '20px',
                                    borderRadius: '12px',
                                    border: '1px solid var(--border-color)',
                                    background: 'var(--panel-bg)',
                                    color: 'var(--text-primary)',
                                    fontFamily: 'monospace',
                                    fontSize: '0.85rem',
                                    lineHeight: '1.6',
                                    resize: 'none',
                                    boxShadow: 'inset 0 4px 10px rgba(0,0,0,0.1)'
                                }}
                            />
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default ToolRegistry;
