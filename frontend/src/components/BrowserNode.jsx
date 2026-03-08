import React, { useState } from 'react';
import { Handle, Position } from 'reactflow';
import axios from 'axios';
import { Search, Globe, ChevronRight, FileText, Zap, ExternalLink, ShieldCheck, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const BrowserNode = ({ data, id }) => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedPage, setSelectedPage] = useState(null);
    const [scraping, setScraping] = useState(false);
    const [digest, setDigest] = useState('');
    const [summarizing, setSummarizing] = useState(false);

    const handleSearch = async () => {
        if (!query) return;
        setLoading(true);
        setDigest('');
        try {
            const resp = await axios.get(`http://localhost:8001/search?q=${encodeURIComponent(query)}`);
            setResults(resp.data);
        } catch (e) {
            console.error("Search failed", e);
        }
        setLoading(false);
    };

    const handleSummarize = async () => {
        if (results.length === 0) return;
        setSummarizing(true);
        try {
            const combinedContent = results.map(r => r.snippet).join("\n\n");
            const resp = await axios.post(`http://localhost:8001/browser/summarize`, {
                query: query,
                content: combinedContent
            });
            setDigest(resp.data.summary);
        } catch (e) {
            console.error("Summarization failed", e);
        }
        setSummarizing(false);
    };

    const handleScrape = async (url) => {
        setScraping(true);
        try {
            const resp = await axios.get(`http://localhost:8001/browser/scrape?url=${encodeURIComponent(url)}`);
            setSelectedPage(resp.data);
        } catch (e) {
            console.error("Scrape failed", e);
        }
        setScraping(false);
    };

    const handleTearAway = (text, title) => {
        if (data.onTearAway) {
            data.onTearAway({ text, title });
        }
    };

    return (
        <div className="card" style={{ 
            width: '450px', 
            minHeight: '400px', 
            border: '2px solid var(--accent-cyan)', 
            padding: 0, 
            background: 'var(--panel-bg)',
            boxShadow: 'var(--card-shadow)',
            display: 'flex',
            flexDirection: 'column'
        }}>
            <Handle type="target" position={Position.Top} style={{ background: 'var(--accent-cyan)' }} />
            
            {/* Browser Header/Search */}
            <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)', background: 'var(--header-bg)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Globe size={18} color="var(--accent-cyan)" />
                        <span style={{ fontSize: '0.8rem', fontWeight: 'bold', letterSpacing: '1px', textTransform: 'uppercase', color: 'var(--text-primary)' }}>Research Browser</span>
                    </div>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        {results.length > 0 && !selectedPage && (
                            <button 
                                className="button-secondary" 
                                onClick={handleSummarize} 
                                disabled={summarizing}
                                style={{ fontSize: '0.65rem', padding: '4px 8px', borderRadius: '12px' }}
                            >
                                {summarizing ? 'SUMMARIZING...' : 'AI DIGEST'}
                            </button>
                        )}
                        <button 
                            onClick={() => data.onDelete && data.onDelete(id)}
                            style={{ background: 'none', border: 'none', color: 'var(--accent-red)', cursor: 'pointer', padding: '2px' }}
                            title="Close Browser"
                        >
                            <X size={18} />
                        </button>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <input 
                        className="input"
                        placeholder="Ask the Swarm anything..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        style={{ flex: 1, padding: '10px 15px', borderRadius: '8px' }}
                    />
                    <button 
                        className="button-primary" 
                        onClick={handleSearch}
                        disabled={loading}
                        style={{ padding: '10px' }}
                    >
                        {loading ? <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity }}><Zap size={20} /></motion.div> : <Search size={20} />}
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '10px', background: 'var(--bg-color)' }}>
                {digest && !selectedPage && (
                    <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        style={{ marginBottom: '15px', padding: '15px', background: 'var(--digest-bg)', border: '1px solid var(--border-color)', borderRadius: '8px' }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <Zap size={14} color="var(--accent-cyan)" />
                                <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--accent-cyan)' }}>AI SWARM DIGEST</span>
                            </div>
                            <button onClick={() => handleTearAway(digest, `${query} - Digest`)} style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', cursor: 'pointer' }} title="Tear away to Canvas">
                                <FileText size={14} />
                            </button>
                        </div>
                        <p style={{ fontSize: '0.85rem', lineHeight: '1.5', opacity: 0.9 }}>{digest}</p>
                    </motion.div>
                )}

                {!selectedPage ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {results.map((res, i) => (
                            <motion.div 
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                key={i} 
                                className="card" 
                                style={{ padding: '12px', cursor: 'pointer', border: '1px solid var(--border-color)', position: 'relative' }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }} onClick={() => handleScrape(res.link)}>
                                    <h4 style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', fontWeight: 'bold' }}>{res.title}</h4>
                                    {res.source_tier === 'High' && <ShieldCheck size={14} color="var(--accent-green)" />}
                                </div>
                                <p style={{ fontSize: '0.75rem', opacity: 0.7, marginBottom: '8px' }} onClick={() => handleScrape(res.link)}>{res.snippet}</p>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div style={{ fontSize: '0.65rem', opacity: 0.85, display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-primary)' }}>
                                        <ExternalLink size={10} /> {res.link.slice(0, 30)}...
                                    </div>
                                    <button onClick={() => handleTearAway(res.snippet, res.title)} style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', cursor: 'pointer', padding: '2px' }} title="Tear away to Canvas">
                                        <FileText size={14} />
                                    </button>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                ) : (
                    <div style={{ padding: '10px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                            <button onClick={() => setSelectedPage(null)} style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
                                <ChevronRight size={14} style={{ rotate: '180deg' }} /> Back
                            </button>
                            <button onClick={() => handleTearAway(selectedPage.content, selectedPage.title)} style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', fontSize: '0.75rem' }}>
                                <FileText size={14} /> EXTRACT TO CANVAS
                            </button>
                        </div>
                        <h3 style={{ fontSize: '1.1rem', marginBottom: '10px', color: 'var(--text-primary)' }}>{selectedPage.title}</h3>
                        <div style={{ fontSize: '0.85rem', lineHeight: '1.6', opacity: 0.9, whiteSpace: 'pre-wrap' }}>
                            {selectedPage.content}
                        </div>
                    </div>
                )}
            </div>

            {/* Footer Status */}
            <div style={{ padding: '10px 20px', borderTop: '1px solid var(--border-color)', fontSize: '0.65rem', display: 'flex', justifyContent: 'space-between', opacity: 0.85, color: 'var(--text-primary)' }}>
                <span>Sources: SearXNG</span>
                <span>Geo-Bias: CO</span>
            </div>

            <Handle type="source" position={Position.Bottom} style={{ background: 'var(--accent-cyan)' }} />
        </div>
    );
};

export default BrowserNode;
