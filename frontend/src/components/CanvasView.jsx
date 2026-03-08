import React, { useEffect, useState, useCallback } from 'react';
import { Tldraw, createShapeId } from '@tldraw/tldraw';
import axios from 'axios';
import { Book, Search, X, ChevronRight, Zap } from 'lucide-react';
import { API_BASE } from '../api.js';
import '@tldraw/tldraw/tldraw.css';

const CanvasView = () => {
  const [editor, setEditor] = useState(null);
  const [showKB, setShowKB] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!editor) return;

    const handleTearAwayEvent = (e) => {
      const { content, x, y } = e.detail;
      editor.createShapes([
        {
          id: createShapeId(),
          type: 'text',
          x: x || 100,
          y: y || 100,
          props: {
            text: content,
            font: 'mono',
            align: 'start',
            size: 's'
          },
        },
      ]);
      // Also add a box behind it for a "card" feel
      editor.createShapes([
        {
          id: createShapeId(),
          type: 'geo',
          x: (x || 100) - 10,
          y: (y || 100) - 10,
          props: {
            geo: 'rectangle',
            w: 300,
            h: 150,
            color: 'light-blue',
            fill: 'semi',
            dash: 'draw'
          },
        }
      ]);
    };

    window.addEventListener('canvas-tear-away', handleTearAwayEvent);
    return () => window.removeEventListener('canvas-tear-away', handleTearAwayEvent);
  }, [editor]);

  const handleKBSearch = async () => {
     if (!searchQuery.trim()) return;
     setSearching(true);
     try {
        const resp = await axios.get(`${API_BASE}/knowledge/search?q=${encodeURIComponent(searchQuery)}`);
        setSearchResults(resp.data.results || []);
     } catch (e) {
        console.error("KB search failed", e);
     }
     setSearching(false);
  };

  const handleDropToCanvas = (result) => {
    if (!editor) return;
    const { content, metadata } = result;
    const text = `[KNOWLEDGE BASE: ${metadata?.source || 'Ref'}]\n\n${content}`;
    
    editor.createShapes([
        {
          id: createShapeId(),
          type: 'text',
          x: 200,
          y: 200,
          props: {
            text: text,
            font: 'mono',
            align: 'start',
            size: 's'
          },
        }
    ]);
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
      <Tldraw 
        inferDarkMode 
        persistenceKey="ai-agent-platform-canvas"
        onMount={(editor) => setEditor(editor)}
      />
      
      {/* KB Trigger Button */}
      <button 
        onClick={() => setShowKB(!showKB)}
        style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 1001, background: 'var(--panel-bg)', border: '1px solid var(--accent-cyan)', color: 'var(--accent-cyan)', borderRadius: '8px', padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', boxShadow: 'var(--card-shadow)' }}
      >
        <Book size={18} /> KNOWLEDGE BASE
      </button>

      {/* KB Sidebar Drawer */}
      {showKB && (
        <div className="glass-effect" style={{ position: 'absolute', top: 0, right: 0, width: '400px', height: '100%', zIndex: 1002, borderLeft: '1px solid var(--accent-cyan)', display: 'flex', flexDirection: 'column', padding: '20px', gap: '20px' }}>
           <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                 <Zap size={20} color="var(--accent-cyan)" />
                 <h3 style={{ margin: 0, color: 'var(--text-primary)', fontSize: '1rem', letterSpacing: '1px' }}>AGENT REFERENCE</h3>
              </div>
              <button onClick={() => setShowKB(false)} style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}><X size={20}/></button>
           </div>

           <div style={{ position: 'relative' }}>
              <input 
                 type="text" 
                 placeholder="Search coding docs, n8n patterns..." 
                 value={searchQuery}
                 onChange={(e) => setSearchQuery(e.target.value)}
                 onKeyDown={(e) => e.key === 'Enter' && handleKBSearch()}
                 style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '10px 40px 10px 15px', color: 'var(--text-primary)', fontSize: '0.9rem' }}
              />
              <Search size={18} color="var(--accent-cyan)" style={{ position: 'absolute', right: '12px', top: '10px', cursor: 'pointer' }} onClick={handleKBSearch} />
           </div>

           <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {searching ? (
                 <div style={{ padding: '20px', textAlign: 'center', opacity: 0.6, fontSize: '0.8rem' }}>Querying RAG vectors...</div>
              ) : searchResults.length > 0 ? (
                 searchResults.map((res, i) => (
                    <div key={i} className="card" style={{ padding: '12px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '8px', position: 'relative', cursor: 'pointer' }} onClick={() => handleDropToCanvas(res)}>
                       <div style={{ fontSize: '0.65rem', color: 'var(--accent-ochre)', marginBottom: '5px' }}>{res.metadata?.category?.toUpperCase()} | {res.metadata?.source}</div>
                       <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: '1.4', opacity: 0.9 }}>{res.content.substring(0, 150)}...</div>
                       <ChevronRight size={14} style={{ position: 'absolute', right: '10px', bottom: '10px', opacity: 0.5 }} />
                    </div>
                 ))
              ) : (
                 <div style={{ padding: '40px 20px', textAlign: 'center', opacity: 0.4, fontSize: '0.8rem' }}>
                    No reference data found.<br/>Try: "n8n trigger", "python loop", "platform soul"
                 </div>
              )}
           </div>
        </div>
      )}

      <div style={{ position: 'absolute', top: '10px', left: '10px', zIndex: 1000, background: 'var(--panel-bg)', padding: '5px 10px', borderRadius: '4px', fontSize: '0.75rem', border: '1px solid var(--accent-cyan)', color: 'var(--accent-cyan)', pointerEvents: 'none' }}>
        TLDRAW CREATIVE CANVAS
      </div>
    </div>
  );
};

export default CanvasView;
