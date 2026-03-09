import React, { useState } from 'react';
import { 
  Library, Search, Upload, FileText, Book, Code, 
  Terminal, CheckCircle2, AlertCircle, Loader2, Play
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { API_BASE } from '../api.js';

const KnowledgeHub = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // 'idle', 'uploading', 'success', 'error'
  const [selectedCategory, setSelectedCategory] = useState('All');

  const categories = [
    { name: 'All', icon: Library, count: 0 },
    { name: 'Coding', icon: Code, count: 0 },
    { name: 'N8N', icon: Terminal, count: 0 },
    { name: 'Architecture', icon: Book, count: 0 },
    { name: 'Project Docs', icon: FileText, count: 0 },
  ];

  const handleSearch = async (e) => {
    const q = e.target.value;
    setSearchQuery(q);
    if (q.length > 2) {
      setIsSearching(true);
      try {
        const res = await axios.get(`${API_BASE}/knowledge/search?q=${q}`);
        setSearchResults(res.data?.data?.results || res.data?.results || []);
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setIsSearching(false);
      }
    } else {
      setSearchResults([]);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', selectedCategory === 'All' ? 'general' : selectedCategory.toLowerCase());

    try {
      await axios.post(`${API_BASE}/knowledge/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadStatus('success');
      setTimeout(() => setUploadStatus(null), 3000);
    } catch (err) {
      console.error("Upload failed:", err);
      setUploadStatus('error');
      setTimeout(() => setUploadStatus(null), 5000);
    }
  };

  const SectionCard = ({ accentColor = 'var(--accent-cyan)', children, style = {} }) => (
      <div className="glass-panel" style={{
          borderTop: `3px solid ${accentColor}`,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: '24px',
          ...style
      }}>
          {children}
      </div>
  );

  const SectionHeader = ({ icon: Icon, title, color }) => (
      <div style={{
          padding: '14px 22px',
          background: 'var(--header-bg)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex', alignItems: 'center', gap: '10px'
      }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
              {Icon && <Icon size={18} color={color} />}
              <span style={{ fontSize: '0.8rem', fontWeight: '900', color, letterSpacing: '1.5px' }}>{title}</span>
          </div>
      </div>
  );

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '24px', overflow: 'hidden', padding: '20px' }}>
      {/* Header Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--accent-cyan)', margin: 0, display: 'flex', alignItems: 'center', gap: '14px' }}>
                <Library size={30} /> KNOWLEDGE HUB
            </h2>
            <p style={{ opacity: 0.6, fontSize: '0.88rem', marginTop: '5px' }}>Manage and search technical reference documentation for your swarm.</p>
        </div>
        
        <div style={{ position: 'relative', width: '400px' }}>
          <input
            type="text"
            className="input"
            placeholder="Search the library... (Cmd+K)"
            value={searchQuery}
            onChange={handleSearch}
            style={{ width: '100%', paddingLeft: '40px', paddingRight: '40px', borderRadius: '16px', background: 'var(--nav-hover-bg)' }}
          />
          <Search style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5, color: 'var(--accent-cyan)' }} size={18} />
          {isSearching && <Loader2 className="spin" style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--accent-cyan)' }} size={18} />}
        </div>
      </div>

      {/* Categories Nav */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '8px', background: 'var(--header-bg)', padding: '6px', borderRadius: '12px', width: 'fit-content' }}>
            {categories.map((cat) => {
              const isActive = selectedCategory === cat.name;
              return (
                <button
                  key={cat.name}
                  onClick={() => setSelectedCategory(cat.name)}
                  style={{ 
                      display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 20px', 
                      borderRadius: '8px', border: 'none', cursor: 'pointer', fontSize: '0.75rem', 
                      fontWeight: '900', letterSpacing: '1px', transition: 'all 0.2s',
                      background: isActive ? 'var(--accent-cyan)' : 'transparent',
                      color: isActive ? 'var(--overlay-heavy-bg)' : 'var(--text-primary)',
                      boxShadow: isActive ? '0 4px 12px rgba(0,255,255,0.2)' : 'none'
                  }}
                >
                  <cat.icon size={16} />
                  {cat.name} {cat.count > 0 && `(${cat.count})`}
                </button>
              );
            })}
          </div>

          <label className="button-primary" style={{ cursor: 'pointer', margin: 0 }}>
            <Upload size={18} /> INGEST NEW DOCUMENT
            <input type="file" style={{ display: 'none' }} onChange={handleFileUpload} accept=".pdf,.md,.txt" />
          </label>
      </div>

      <AnimatePresence>
        {uploadStatus && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={{ 
              padding: '12px 20px', 
              borderRadius: '12px', 
              display: 'flex', alignItems: 'center', gap: '10px',
              background: uploadStatus === 'error' ? 'rgba(244,67,54,0.1)' : 'rgba(76,175,80,0.1)',
              border: `1px solid ${uploadStatus === 'error' ? 'var(--status-error)' : 'var(--status-idle)'}` 
            }}
          >
            {uploadStatus === 'uploading' && <Loader2 size={16} className="spin" color="var(--accent-cyan)" />}
            {uploadStatus === 'success' && <CheckCircle2 size={16} color="var(--status-idle)" />}
            {uploadStatus === 'error' && <AlertCircle size={16} color="var(--status-error)" />}
            <span style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>
              {uploadStatus === 'uploading' ? 'Analyzing and Embedding Document...' : 
               uploadStatus === 'success' ? 'Document Ingested and Vectorized Successfully!' : 'Upload Failed. Check Server Logs.'}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Grid Content */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px', paddingRight: '10px' }} className="custom-scrollbar">
        {searchResults.length > 0 ? (
          <SectionCard accentColor="var(--accent-cyan)">
             <SectionHeader icon={Search} title="SEARCH RESULTS" color="var(--accent-cyan)" />
             <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {searchResults.map((result, i) => (
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    key={i}
                    style={{
                      padding: '16px 20px',
                      background: 'var(--nav-hover-bg)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '16px',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent-cyan)'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-color)'}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ padding: '8px', background: 'rgba(0,255,255,0.1)', borderRadius: '10px' }}>
                          <FileText size={18} color="var(--accent-cyan)" />
                        </div>
                        <div>
                          <p style={{ margin: 0, fontWeight: '800', fontSize: '1rem', color: 'var(--text-primary)' }}>{result.metadata?.filename || 'Unknown File'}</p>
                          <p style={{ margin: 0, fontSize: '0.7rem', opacity: 0.6 }}>Score: {Math.round((result.score || 0) * 100)}% Match | Chunk #{result.metadata?.chunk_index || 0}</p>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.65rem', fontWeight: '900', letterSpacing: '1px', textTransform: 'uppercase', background: 'var(--panel-bg)', padding: '4px 10px', borderRadius: '12px', border: '1px solid var(--border-color)', color: 'var(--accent-ochre)' }}>
                        {result.metadata?.category || 'REFERENCE'}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.85rem', lineHeight: 1.6, opacity: 0.8, background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '10px', borderLeft: '3px solid var(--accent-cyan)' }}>
                      "...{result.content.substring(0, 300)}..."
                    </p>
                  </motion.div>
                ))}
             </div>
          </SectionCard>
        ) : searchQuery ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: 0.5, padding: '40px' }}>
             <Search size={48} style={{ marginBottom: '20px' }} />
             <h3 style={{ fontSize: '1.2rem', fontWeight: '900', margin: '0 0 8px 0' }}>NO MATCHES FOUND</h3>
             <p style={{ margin: 0, fontSize: '0.9rem' }}>Try generic terms or check category filters.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '24px' }}>
             
             {/* Main Hero Card */}
             <div style={{ gridColumn: 'span 12' }}>
                <SectionCard accentColor="var(--accent-cyan)" style={{ position: 'relative' }}>
                    <div style={{ padding: '40px', position: 'relative', zIndex: 1 }}>
                        <div style={{ width: '60px', height: '60px', background: 'var(--accent-cyan)', borderRadius: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px', boxShadow: '0 10px 30px rgba(0,255,255,0.2)' }}>
                            <Library size={32} color="#000" />
                        </div>
                        <h3 style={{ fontSize: '2rem', fontWeight: '900', color: 'var(--text-primary)', margin: '0 0 16px 0', letterSpacing: '-0.5px' }}>INTELLIGENT REFERENCE LIBRARY</h3>
                        <p style={{ fontSize: '1.05rem', lineHeight: 1.6, opacity: 0.8, maxWidth: '600px', margin: '0 0 30px 0' }}>
                           This library is shared globally across your swarm. When an agent needs a technical specification, workflow node, or coding rule, they will perform Vector Retrieval (RAG) here first.
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                            <span style={{ padding: '6px 16px', background: 'rgba(0,255,255,0.1)', color: 'var(--accent-cyan)', borderRadius: '20px', fontSize: '0.75rem', fontWeight: '900', letterSpacing: '1px', border: '1px solid rgba(0,255,255,0.3)' }}>RAG ENABLED</span>
                            <span style={{ padding: '6px 16px', background: 'rgba(212,163,115,0.1)', color: 'var(--accent-ochre)', borderRadius: '20px', fontSize: '0.75rem', fontWeight: '900', letterSpacing: '1px', border: '1px solid rgba(212,163,115,0.3)' }}>QDRANT VECTOR SEARCH</span>
                            <span style={{ padding: '6px 16px', background: 'rgba(168,85,247,0.1)', color: 'var(--accent-purple)', borderRadius: '20px', fontSize: '0.75rem', fontWeight: '900', letterSpacing: '1px', border: '1px solid rgba(168,85,247,0.3)' }}>BGE-LARGE EMBEDDINGS</span>
                        </div>
                    </div>
                    <Library size={300} style={{ position: 'absolute', right: '-40px', bottom: '-40px', opacity: 0.03, transform: 'rotate(-15deg)' }} />
                </SectionCard>
             </div>

             {/* Bento Block 1 */}
             <div style={{ gridColumn: 'span 6' }}>
                <SectionCard accentColor="var(--accent-green)" style={{ height: '100%' }}>
                    <SectionHeader icon={Code} title="CODING STANDARDS" color="var(--accent-green)" />
                    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%' }}>
                        <p style={{ margin: '0 0 20px 0', fontSize: '0.9rem', opacity: 0.8, lineHeight: 1.6, flex: 1 }}>
                          Latest React, JS, and FastAPI best practices are automatically indexed. Add your own coding constraints dynamically via the UI to instruct agents.
                        </p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.75rem', color: 'var(--accent-green)', fontWeight: '800' }}>
                            <CheckCircle2 size={16} /> UPVOTED BY ARCHITECT SWARM
                        </div>
                    </div>
                </SectionCard>
             </div>

             {/* Bento Block 2 */}
             <div style={{ gridColumn: 'span 6' }}>
                <SectionCard accentColor="var(--accent-purple)" style={{ height: '100%' }}>
                    <SectionHeader icon={Terminal} title="N8N WORKFLOW RULES" color="var(--accent-purple)" />
                    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%' }}>
                        <p style={{ margin: '0 0 20px 0', fontSize: '0.9rem', opacity: 0.8, lineHeight: 1.6, flex: 1 }}>
                          Documentation for custom nodes and external API structures used in executing automated workflows.
                        </p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.75rem', color: 'var(--accent-purple)', fontWeight: '800' }}>
                            <CheckCircle2 size={16} /> VERIFIED BY DEV-OPS EXPERT
                        </div>
                    </div>
                </SectionCard>
             </div>

          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeHub;
