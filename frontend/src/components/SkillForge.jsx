import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Hammer, Zap, ChevronRight, ChevronLeft, ExternalLink,
    Globe, Package, Terminal, Shield, CheckCircle2, Cpu,
    Brain, Code, Sparkles, Loader2
} from 'lucide-react';
import { API_BASE } from '../api.js';

// ── Skill type definitions ─────────────────────────────────────────────────────
const SKILL_TYPES = [
    {
        id: 'skill',
        label: 'Native Skill',
        icon: Cpu,
        color: 'var(--accent-cyan)',
        desc: 'Pure Python — local logic, no external protocol. Best for libraries like python-pptx, Pillow, etc.',
        example: 'PPTX generator, image annotator, CSV processor',
    },
    {
        id: 'mcp',
        label: 'MCP Server',
        icon: Terminal,
        color: 'var(--accent-purple)',
        desc: 'Standard Model Context Protocol server. The AI already understands the protocol — just configure the connection.',
        example: 'Filesystem access, browser control, code execution',
    },
    {
        id: 'hybrid',
        label: 'Hybrid',
        icon: Brain,
        color: 'var(--accent-ochre)',
        desc: 'Complex external systems: combines native Python control + MCP server + API documentation. Best for full platforms.',
        example: 'n8n, Slack, GitHub, Notion, Salesforce',
    },
];

// ── Wizard step definitions (by skill type) ───────────────────────────────────
const STEPS_BY_TYPE = {
    skill: [
        { id: 'type',         title: 'Skill Type',      subtitle: 'What kind of capability are you building?' },
        { id: 'name',         title: 'Name & Purpose',  subtitle: 'What does this skill do?' },
        { id: 'library',      title: 'Python Library',  subtitle: 'What Python package powers this?' },
        { id: 'methods',      title: 'Execution Nodes', subtitle: 'What can it do? (methods the agent will call)' },
        { id: 'docs',         title: 'Reference Docs',  subtitle: 'Where should the agent look for help?' },
        { id: 'review',       title: 'Review & Forge',  subtitle: 'Final review before assembly.' },
    ],
    mcp: [
        { id: 'type',         title: 'Skill Type',      subtitle: 'What kind of capability are you building?' },
        { id: 'name',         title: 'Name & Purpose',  subtitle: 'What does this skill do?' },
        { id: 'mcp_config',   title: 'MCP Config',      subtitle: 'Server path and environment variables.' },
        { id: 'review',       title: 'Review & Forge',  subtitle: 'Final review before assembly.' },
    ],
    hybrid: [
        { id: 'type',         title: 'Skill Type',      subtitle: 'What kind of capability are you building?' },
        { id: 'name',         title: 'Name & Purpose',  subtitle: 'What does this skill do?' },
        { id: 'mcp_config',   title: 'MCP Config',      subtitle: 'Server path and environment variables.' },
        { id: 'api_calls',    title: 'API Commands',    subtitle: 'Key REST calls the agent should know.' },
        { id: 'docs',         title: 'Reference Docs',  subtitle: 'External documentation links.' },
        { id: 'review',       title: 'Review & Forge',  subtitle: 'Final review before assembly.' },
    ],
};

// ── Shared field input with AI-assist ─────────────────────────────────────────
const AiField = ({ label, helpText, helpUrl, value, onChange, placeholder, multiline, aiContext, onAiAssist, loading }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '1px' }}>{label}</label>
            {helpUrl && (
                <a href={helpUrl} target="_blank" rel="noreferrer"
                    style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.65rem', color: 'var(--accent-cyan)', textDecoration: 'none', opacity: 0.8 }}>
                    <ExternalLink size={10} /> DOCS
                </a>
            )}
        </div>
        {helpText && <p style={{ margin: 0, fontSize: '0.75rem', opacity: 0.6, lineHeight: 1.5 }}>{helpText}</p>}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
            {multiline ? (
                <textarea value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
                    className="input" rows={4}
                    style={{ flex: 1, resize: 'vertical', fontFamily: 'monospace', fontSize: '0.82rem', lineHeight: 1.6 }}
                />
            ) : (
                <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
                    className="input" style={{ flex: 1 }}
                />
            )}
            <button onClick={() => onAiAssist(aiContext)} disabled={loading}
                title="Ask Guide to help with this field"
                style={{ padding: '10px 12px', borderRadius: '10px', border: '1px solid rgba(251,191,36,0.3)', background: 'rgba(251,191,36,0.08)', color: 'var(--accent-ochre)', cursor: loading ? 'wait' : 'pointer', flexShrink: 0 }}>
                {loading ? <Loader2 size={15} className="spin" /> : <Zap size={15} />}
            </button>
        </div>
    </div>
);

// ── Main Component ─────────────────────────────────────────────────────────────
const SkillForge = () => {
    const [skillType, setSkillType] = useState('skill');
    const [stepIdx, setStepIdx] = useState(0);
    const [fieldLoading, setFieldLoading] = useState({});
    const [assembling, setAssembling] = useState(false);
    const [assembled, setAssembled] = useState(null);
    const [guideMessages, setGuideMessages] = useState([]);
    const [reconLoading, setReconLoading] = useState(false);
    const [reconData, setReconData] = useState(null);

    // Draft state
    const [draft, setDraft] = useState({
        name: '',
        description: '',
        library: '',        // skill only
        methods: '',        // skill / hybrid — freetext list of method names + docs
        mcp_path: '',       // mcp / hybrid
        mcp_source_url: '', // mcp / hybrid — Link to Git Repository or Homepage
        mcp_env_vars: '',   // mcp / hybrid
        api_calls: '',      // hybrid only
        docs_links: '',     // skill / hybrid
    });

    const steps = STEPS_BY_TYPE[skillType];
    const currentStep = steps[stepIdx];

    const setField = (key, val) => setDraft(d => ({ ...d, [key]: val }));

    // ── AI-assist per field ────────────────────────────────────────────────────
    const aiAssist = async (context) => {
        const key = context.field;
        setFieldLoading(f => ({ ...f, [key]: true }));
        try {
            const prompt = `The user is building a ${skillType} skill called "${draft.name || 'Untitled'}". Help with the field "${context.label}". Current value: "${context.value || 'empty'}". ${context.hint || ''}`;
            const resp = await axios.post(`${API_BASE}/forge/interview`, {
                prompt,
                history: [],
                current_preview: { name: draft.name, type: skillType, ...draft }
            });
            const msg = resp.data.response || resp.data.message || '';
            setGuideMessages(m => [...m, { field: context.label, text: msg }]);
        } catch (e) {
            setGuideMessages(m => [...m, { field: context.label, text: 'Guide is unavailable right now. Try again.' }]);
        }
    };

    // ── Deep Recon Automation ──────────────────────────────────────────────────
    const triggerRecon = async () => {
        if (!draft.name || !draft.description) return;
        setReconLoading(true);
        setReconData(null);
        try {
            const resp = await axios.post(`${API_BASE}/forge/interview`, {
                prompt: '/recon',
                history: [],
                current_preview: { name: draft.name, type: skillType, ...draft }
            });
            const update = resp.data.preview_update;
            if (update) {
                setReconData(update);
                setGuideMessages(m => [...m, { 
                    field: 'RECONNAISSANCE', 
                    text: resp.data.response || "Deep Recon complete. Found official sources and capability breakdowns." 
                }]);
            }
        } catch (e) {
            console.error("Recon failed", e);
        }
        setReconLoading(false);
    };

    const hydrateFromRecon = () => {
        if (!reconData) return;
        setDraft(d => ({ ...d, ...reconData }));
        setReconData(null); // Clear after use
    };

    // ── Assemble ───────────────────────────────────────────────────────────────
    const handleAssemble = async () => {
        setAssembling(true);
        try {
            const resp = await axios.post(`${API_BASE}/forge/assemble`, {
                preview: {
                    name: draft.name,
                    type: skillType,
                    subtype: skillType,
                    description: draft.description,
                    architecture: `# ${draft.name}\n\n${draft.description}\n\n# Methods\n${draft.methods}\n\n# Dependencies\n${draft.library}`,
                    docs_links: draft.docs_links.split('\n').filter(Boolean).map(l => ({ label: l, url: l })),
                    mcp_path: draft.mcp_path,
                    mcp_env_vars: draft.mcp_env_vars.split('\n').filter(Boolean),
                    sample_calls: draft.api_calls.split('\n').filter(Boolean).map(l => ({ action: l, endpoint: '', notes: '' })),
                }
            });
            setAssembled(resp.data);
        } catch (e) {
            setAssembled({ error: 'Assembly failed. Check your backend connection.' });
        }
        setAssembling(false);
    };

    // ── Step content renderer ──────────────────────────────────────────────────
    const renderStep = () => {
        switch (currentStep.id) {

            case 'type':
                return (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                        {SKILL_TYPES.map(t => {
                            const Icon = t.icon;
                            const selected = skillType === t.id;
                            return (
                                <motion.button key={t.id} whileHover={{ scale: 1.01 }}
                                    onClick={() => { setSkillType(t.id); setStepIdx(0); }}
                                    style={{ background: selected ? `${t.color}12` : 'var(--nav-hover-bg)', border: `2px solid ${selected ? t.color : 'var(--border-color)'}`, borderRadius: '12px', padding: '18px 20px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s' }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                                        <div style={{ padding: '10px', borderRadius: '10px', background: `${t.color}18`, border: `1px solid ${t.color}44`, flexShrink: 0 }}>
                                            <Icon size={20} color={t.color} />
                                        </div>
                                        <div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                                <span style={{ fontWeight: '900', fontSize: '0.95rem', color: selected ? t.color : 'var(--text-primary)' }}>{t.label}</span>
                                                {selected && <span style={{ fontSize: '0.6rem', fontWeight: '900', padding: '1px 8px', borderRadius: '20px', background: `${t.color}22`, color: t.color, border: `1px solid ${t.color}55` }}>SELECTED</span>}
                                            </div>
                                            <p style={{ margin: '0 0 6px 0', fontSize: '0.82rem', opacity: 0.75, lineHeight: 1.5 }}>{t.desc}</p>
                                            <span style={{ fontSize: '0.7rem', opacity: 0.5, fontStyle: 'italic' }}>e.g. {t.example}</span>
                                        </div>
                                    </div>
                                </motion.button>
                            );
                        })}
                    </div>
                );

            case 'name':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <AiField label="SKILL NAME" placeholder="e.g. pptx_expert, slack_notifier, n8n_control"
                            helpText="Use lowercase_underscore format. This becomes the Python filename and the registry entry name."
                            value={draft.name} onChange={v => setField('name', v)}
                            aiContext={{ field: 'name', label: 'Skill Name', value: draft.name, hint: 'Suggest a clean Python module name matching the purpose.' }}
                            onAiAssist={aiAssist} loading={fieldLoading['name']}
                        />
                        <AiField label="DESCRIPTION" placeholder="What does this skill do? What should an agent know before calling it?"
                            helpText="This text appears in the Capability Overview panel and is embedded into Qdrant for semantic retrieval."
                            multiline value={draft.description} onChange={v => setField('description', v)}
                            aiContext={{ field: 'description', label: 'Description', value: draft.description, hint: 'Write a clear 2-3 sentence capability overview.' }}
                            onAiAssist={aiAssist} loading={fieldLoading['description']}
                        />
                        
                        <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'flex-end' }}>
                            <button 
                                onClick={triggerRecon}
                                disabled={reconLoading || !draft.name || !draft.description}
                                className="button-primary"
                                style={{ 
                                    background: 'var(--accent-purple)', 
                                    padding: '10px 20px', 
                                    fontSize: '0.8rem',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px',
                                    boxShadow: '0 4px 14px rgba(168,85,247,0.3)'
                                }}
                            >
                                {reconLoading ? <Loader2 size={16} className="spin" /> : <Sparkles size={16} />}
                                START DEEP RECON
                            </button>
                        </div>

                        {reconData && (
                            <motion.div 
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                style={{ 
                                    marginTop: '20px', 
                                    padding: '20px', 
                                    borderRadius: '12px', 
                                    background: 'rgba(168,85,247,0.1)', 
                                    border: '1px solid rgba(168,85,247,0.3)',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '12px'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-purple)' }}>
                                    <Brain size={20} />
                                    <strong style={{ fontSize: '0.9rem', letterSpacing: '1px' }}>RECON DISCOVERY INSIGHT</strong>
                                </div>
                                <p style={{ margin: 0, fontSize: '0.82rem', opacity: 0.8, lineHeight: 1.5 }}>
                                    I've analyzed the ecosystem and found an official repository and documentation. 
                                    I can automatically hydrate your "Methods", "Source URL", and "Reference Docs" with premium Steroids-formatted data.
                                </p>
                                <button 
                                    onClick={hydrateFromRecon}
                                    style={{ 
                                        padding: '10px', 
                                        borderRadius: '8px', 
                                        background: 'var(--accent-cyan)', 
                                        color: '#000', 
                                        border: 'none', 
                                        fontWeight: '900', 
                                        fontSize: '0.75rem', 
                                        cursor: 'pointer' 
                                    }}
                                >
                                    APPLY DISCOVERY (HYDRATE FIELDS)
                                </button>
                            </motion.div>
                        )}
                    </div>
                );

            case 'library':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <AiField label="PYTHON LIBRARY / PACKAGE"
                            placeholder="e.g. python-pptx, Pillow, httpx, playwright"
                            helpText="What pip package does this skill require? This gets added to requirements.txt."
                            helpUrl="https://pypi.org/"
                            value={draft.library} onChange={v => setField('library', v)}
                            aiContext={{ field: 'library', label: 'Python Library', value: draft.library, hint: 'What pip package name should be used? Give the exact PyPI name.' }}
                            onAiAssist={aiAssist} loading={fieldLoading['library']}
                        />
                    </div>
                );

            case 'methods':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <AiField label="EXECUTION NODES (METHODS) — STEROIDS FORMAT"
                            placeholder={"create_presentation(template_path) — Creates a premium slide deck\nArgs:\n  template_path (str): Local path to .pptx\nReturns:\n  dict: Success status\nUsage Example:\n  await execute('create_presentation', {'template_path': 'base.pptx'})"}
                            helpText="List each method in the 'Steroids' format: name(params) — desc + Google-style Args/Returns + Usage Example. Guide will help you expand basic names into this format."
                            multiline value={draft.methods} onChange={v => setField('methods', v)}
                            aiContext={{ field: 'methods', label: 'Methods', value: draft.methods, hint: `Suggest 4-6 premium async methods in the 'Skills on Steroids' format. Include Google-style docstrings (Args, Returns) and Usage Examples for each.` }}
                            onAiAssist={aiAssist} loading={fieldLoading['methods']}
                        />
                    </div>
                );

            case 'mcp_config':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <AiField label="MCP SERVER PATH"
                            placeholder="e.g. npx @modelcontextprotocol/server-filesystem  OR  ~/gemini_workspace/mcp_servers/n8n-mcp/node_modules/.bin/n8n-mcp"
                            helpText="Full command or binary path to start the MCP server. Use npx for official servers."
                            helpUrl="https://github.com/modelcontextprotocol/servers"
                            value={draft.mcp_path} onChange={v => setField('mcp_path', v)}
                            aiContext={{ field: 'mcp_path', label: 'MCP Server Path', value: draft.mcp_path, hint: `What is the correct npx command or binary path to start the MCP server for ${draft.name}?` }}
                            onAiAssist={aiAssist} loading={fieldLoading['mcp_path']}
                        />
                        <AiField label="SOURCE / HOMEPAGE URL"
                            placeholder="e.g. https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem"
                            helpText="Link to the official repository or homepage. This helps the agent find detailed capabilities."
                            value={draft.mcp_source_url} onChange={v => setField('mcp_source_url', v)}
                            aiContext={{ field: 'mcp_source_url', label: 'Source URL', value: draft.mcp_source_url, hint: `What is the official GitHub or documentation link for the ${draft.name} MCP server?` }}
                            onAiAssist={aiAssist} loading={fieldLoading['mcp_source_url']}
                        />
                        <AiField label="ENV VARS (one per line)"
                            placeholder={"N8N_API_URL=http://localhost:5678/api/v1\nN8N_API_KEY=your_key_here"}
                            helpText="Required environment variables. Leave empty if none needed."
                            multiline value={draft.mcp_env_vars} onChange={v => setField('mcp_env_vars', v)}
                            aiContext={{ field: 'mcp_env_vars', label: 'Environment Variables', value: draft.mcp_env_vars, hint: `What environment variables are needed to run the MCP server for ${draft.name}? List as KEY=example_value.` }}
                            onAiAssist={aiAssist} loading={fieldLoading['mcp_env_vars']}
                        />
                    </div>
                );

            case 'api_calls':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <AiField label="KEY API COMMANDS"
                            placeholder={"List Workflows | GET /workflows | Returns all workflows\nTrigger Webhook | POST /webhooks/{path} | Fires a workflow\nGet Executions | GET /executions | Filter by workflowId, status"}
                            helpText="Format each line as: Action | Endpoint | Notes. These appear in the API Quick-Commands table."
                            multiline value={draft.api_calls} onChange={v => setField('api_calls', v)}
                            aiContext={{ field: 'api_calls', label: 'API Commands', value: draft.api_calls, hint: `List 5-8 frequently used REST API calls for ${draft.name}. Format: Action | METHOD /endpoint | brief note` }}
                            onAiAssist={aiAssist} loading={fieldLoading['api_calls']}
                        />
                    </div>
                );

            case 'docs':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <AiField label="REFERENCE DOCS (one URL per line)"
                            placeholder={"https://python-pptx.readthedocs.io/en/latest/\nhttps://learn.microsoft.com/en-us/office/open-xml/open-xml-sdk\nhttps://slidesgo.com/design-tips"}
                            helpText="Documentation, API references, design guides. These appear as clickable link rows in the Registry."
                            multiline value={draft.docs_links} onChange={v => setField('docs_links', v)}
                            aiContext={{ field: 'docs_links', label: 'Reference Docs', value: draft.docs_links, hint: `Search the web and list 4-6 high-quality documentation URLs for ${draft.name || draft.library}. Include API ref, design guides, examples.` }}
                            onAiAssist={aiAssist} loading={fieldLoading['docs_links']}
                        />
                    </div>
                );

            case 'review':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        {[
                            { label: 'NAME', value: draft.name || '—' },
                            { label: 'TYPE', value: skillType.toUpperCase() },
                            { label: 'DESCRIPTION', value: draft.description || '—' },
                            draft.library && { label: 'LIBRARY', value: draft.library },
                            draft.mcp_path && { label: 'MCP PATH', value: draft.mcp_path },
                            draft.methods && { label: 'METHODS', value: draft.methods.split('\n').length + ' defined' },
                            draft.api_calls && { label: 'API CALLS', value: draft.api_calls.split('\n').filter(Boolean).length + ' defined' },
                            draft.docs_links && { label: 'DOCS LINKS', value: draft.docs_links.split('\n').filter(Boolean).length + ' links' },
                        ].filter(Boolean).map((row, i) => (
                                <div key={i} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', padding: '12px 16px', borderRadius: '8px', background: 'var(--nav-hover-bg)', border: '1px solid var(--border-color)' }}>
                                <span style={{ fontSize: '0.6rem', fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '1.5px', minWidth: '80px', paddingTop: '2px' }}>{row.label}</span>
                                <span style={{ fontSize: '0.85rem', opacity: 0.9, lineHeight: 1.5 }}>{row.value}</span>
                            </div>
                        ))}

                        {assembled ? (
                            assembled.error ? (
                                <div style={{ padding: '16px', borderRadius: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontSize: '0.85rem' }}>
                                    ⚠ {assembled.error}
                                </div>
                            ) : (
                                <div style={{ padding: '16px', borderRadius: '10px', background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.3)', color: 'var(--accent-green)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <CheckCircle2 size={18} /> {assembled.message || 'Skill assembled successfully!'}
                                </div>
                            )
                        ) : (
                            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                                onClick={handleAssemble} disabled={assembling || !draft.name}
                                style={{ padding: '16px', borderRadius: '12px', background: draft.name ? 'var(--accent-ochre)' : 'rgba(251,191,36,0.2)', color: draft.name ? 'var(--overlay-heavy-bg)' : 'var(--accent-ochre)', border: 'none', cursor: draft.name ? 'pointer' : 'not-allowed', fontWeight: '900', fontSize: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', marginTop: '6px' }}
                            >
                                {assembling ? <><Loader2 size={18} className="spin" /> ASSEMBLING…</> : <><Hammer size={18} /> FORGE SKILL</>}
                            </motion.button>
                        )}
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div style={{ height: '100%', display: 'grid', gridTemplateColumns: '1fr 340px', gap: '24px', overflow: 'hidden', padding: '20px' }}>

            {/* ── LEFT: Wizard ── */}
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                {/* Progress bar */}
                <div style={{ display: 'flex', gap: '6px', marginBottom: '20px' }}>
                    {steps.map((s, i) => (
                        <div key={s.id} onClick={() => i < stepIdx && setStepIdx(i)}
                            style={{ flex: 1, height: '3px', borderRadius: '2px', background: i <= stepIdx ? 'var(--accent-ochre)' : 'var(--border-color)', cursor: i < stepIdx ? 'pointer' : 'default', transition: 'background 0.2s' }}
                        />
                    ))}
                </div>

                {/* Step card */}
                <div className="card" style={{ padding: '28px', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <div style={{ marginBottom: '22px' }}>
                        <span style={{ fontSize: '0.62rem', fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '1.5px', opacity: 0.7 }}>STEP {stepIdx + 1} OF {steps.length}</span>
                        <h2 style={{ margin: '4px 0 6px 0', fontSize: '1.4rem', fontWeight: '900', color: 'var(--text-primary)' }}>{currentStep.title}</h2>
                        <p style={{ margin: 0, fontSize: '0.88rem', opacity: 0.65 }}>{currentStep.subtitle}</p>
                    </div>

                    <div style={{ flex: 1, overflowY: 'auto', paddingRight: '2px' }}>
                        <AnimatePresence mode="wait">
                            <motion.div key={currentStep.id}
                                initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }}
                                transition={{ duration: 0.15 }}
                            >
                                {renderStep()}
                            </motion.div>
                        </AnimatePresence>
                    </div>

                    {/* Nav */}
                    <div style={{ display: 'flex', gap: '10px', marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
                        <button onClick={() => setStepIdx(i => Math.max(0, i - 1))} disabled={stepIdx === 0}
                            className="button-secondary" style={{ display: 'flex', alignItems: 'center', gap: '6px', opacity: stepIdx === 0 ? 0.3 : 1 }}>
                            <ChevronLeft size={16} /> BACK
                        </button>
                        {stepIdx < steps.length - 1 && (
                            <button onClick={() => setStepIdx(i => Math.min(steps.length - 1, i + 1))}
                                className="button-primary" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', background: 'var(--accent-ochre)', color: 'var(--overlay-heavy-bg)' }}>
                                NEXT <ChevronRight size={16} />
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* ── RIGHT: Guide sidebar ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', overflow: 'hidden' }}>
                {/* Guide header */}
                <div className="card" style={{ padding: '18px 20px', background: 'var(--panel-bg)', border: '2px solid var(--accent-ochre)', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <img src="/ehecatl.png" style={{ width: '52px', height: '52px', borderRadius: '50%', border: '2px solid var(--accent-ochre)' }} alt="Guide" />
                    <div>
                        <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: '900', color: 'var(--accent-ochre)' }}>GUIDE</h3>
                        <p style={{ margin: 0, fontSize: '0.72rem', opacity: 0.6 }}>AI-powered field assist. Hit <Zap size={10} style={{ display: 'inline', verticalAlign: 'middle' }} /> on any field for help.</p>
                    </div>
                </div>

                {/* Guide messages */}
                <div className="card" style={{ flex: 1, overflowY: 'auto', padding: '14px', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {guideMessages.length === 0 ? (
                        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '10px', opacity: 0.4 }}>
                            <Sparkles size={28} />
                            <p style={{ fontSize: '0.78rem', textAlign: 'center', lineHeight: 1.5 }}>Use the ⚡ button on any field to get AI suggestions, documentation links, and syntax help.</p>
                        </div>
                    ) : (
                        <AnimatePresence>
                            {guideMessages.map((m, i) => (
                                <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                                    style={{ padding: '12px 14px', borderRadius: '10px', background: 'var(--accent-translucent)', border: '1px solid var(--border-color)' }}>
                                    <span style={{ fontSize: '0.6rem', fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '1px', opacity: 0.7 }}>{m.field}</span>
                                    <p style={{ margin: '5px 0 0 0', fontSize: '0.82rem', lineHeight: 1.6, opacity: 0.9 }}>{m.text}</p>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    )}
                </div>

                {/* Safety notice */}
                <div style={{ padding: '12px 16px', borderRadius: '10px', background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.2)', display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                    <Shield size={14} color="var(--accent-green)" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>Skills are written to <code style={{ background: 'var(--nav-hover-bg)', padding: '1px 5px', borderRadius: '3px', fontSize: '0.65rem' }}>sandbox/</code> and Qdrant-indexed. Promote manually to <code style={{ background: 'var(--nav-hover-bg)', padding: '1px 5px', borderRadius: '3px', fontSize: '0.65rem' }}>src/skills/</code> after testing.</p>
                </div>
            </div>
        </div>
    );
};

export default SkillForge;
