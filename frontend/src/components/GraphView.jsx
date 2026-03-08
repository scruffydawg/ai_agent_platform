import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, { 
  addEdge, 
  Background, 
  useNodesState, 
  useEdgesState,
  Handle,
  Position
} from 'reactflow';
import axios from 'axios';
import { Edit2, Plus, X, Save, Zap, Activity, Shield, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import 'reactflow/dist/style.css';

import { API_BASE } from '../api.js';

const SoulNode = ({ data, id }) => (
  <motion.div 
    whileHover={{ y: -5, scale: 1.02 }}
    className="card glass-panel" 
    style={{ 
      padding: '16px', 
      background: 'var(--panel-bg)', 
      border: '1px solid var(--border-color)', 
      borderRadius: '20px', 
      width: '200px',
      position: 'relative',
      boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
      overflow: 'hidden'
    }}
  >
    <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '4px', background: 'linear-gradient(90deg, transparent, var(--accent-ochre), transparent)', opacity: 0.5 }}></div>
    
    <Handle type="target" position={Position.Top} style={{ background: 'var(--accent-cyan)', border: 'none', width: '8px', height: '8px' }} />
    <Handle type="source" position={Position.Bottom} style={{ background: 'var(--accent-cyan)', border: 'none', width: '8px', height: '8px' }} />
    
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '15px' }}>
      <div style={{ padding: '8px', borderRadius: '10px', background: 'rgba(212, 163, 115, 0.1)', display: 'flex' }}>
        <Zap size={18} color="var(--accent-ochre)" />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontWeight: '900', fontSize: '0.95rem', color: 'var(--text-primary)', letterSpacing: '0.5px' }}>{data.label.toUpperCase()}</span>
        <span style={{ fontSize: '0.65rem', color: 'var(--accent-ochre)', fontWeight: 'bold' }}>ACTIVE SOUL</span>
      </div>
      <button 
        onClick={(e) => { e.stopPropagation(); data.onDelete(data.label); }}
        style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px', opacity: 0.5 }}
        onMouseOver={(e) => e.target.style.opacity = 1}
        onMouseOut={(e) => e.target.style.opacity = 0.5}
        title="Dissolve Expert"
      >
        <X size={16} />
      </button>
    </div>
    
    <p style={{ fontSize: '0.75rem', lineHeight: '1.4', opacity: 0.8, marginBottom: '20px', color: 'var(--text-primary)', fontStyle: 'italic' }}>
      "{data.role || 'Dedicated Swarm Specialist'}"
    </p>
    
    <button 
      onClick={() => data.onEdit(data.label)}
      className="action-button" 
      style={{ width: '100%', justifyContent: 'center', background: 'rgba(212, 163, 115, 0.05)', color: 'var(--accent-ochre)', border: '1px solid rgba(212, 163, 115, 0.2)' }}
    >
      <Sparkles size={14} /> REVEAL SOUL
    </button>
  </motion.div>
);

const nodeTypes = {
  soul: SoulNode,
  sticky: ({ data }) => (
    <div className="card" style={{ padding: '15px', background: 'var(--accent-cyan)', color: 'var(--overlay-heavy-bg)', borderRadius: '8px', width: '250px' }}>
      <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', fontWeight: 'bold' }}>{data.title}</h4>
      <p style={{ margin: 0, fontSize: '0.8rem', lineHeight: '1.4' }}>{data.text}</p>
    </div>
  )
};

const SoulEditor = ({ name, onClose }) => {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [consultMessages, setConsultMessages] = useState([]);
  const [consultInput, setConsultInput] = useState('');
  const [consulting, setConsulting] = useState(false);

  useEffect(() => {
    const fetchSoul = async () => {
      try {
        const resp = await axios.get(`${API_BASE}/swarm/expert/${name}`);
        setContent(resp.data.soul);
      } catch (e) {
        console.error("Failed to fetch soul", e);
      }
      setLoading(false);
    };
    fetchSoul();
  }, [name]);

  const handleSave = async () => {
    try {
      await axios.post(`${API_BASE}/swarm/expert/${name}`, { soul: content });
      alert(`Soul of ${name} crystallized.`);
      onClose();
    } catch (e) {
      alert("Failed to save soul.");
    }
  };

  const handleSendConsult = async () => {
    if (!consultInput.trim() || consulting) return;
    
    const userMsg = { role: 'user', content: consultInput };
    setConsultMessages(prev => [...prev, userMsg]);
    setConsultInput('');
    setConsulting(true);

    try {
      const resp = await axios.post(`${API_BASE}/swarm/consult`, {
        agent_name: name,
        current_soul: content,
        messages: [...consultMessages, userMsg]
      });
      setConsultMessages(prev => [...prev, { role: 'assistant', content: resp.data.response }]);
    } catch (e) {
      setConsultMessages(prev => [...prev, { role: 'assistant', content: "Failed to connect to the Identity Architect." }]);
    } finally {
      setConsulting(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'var(--overlay-bg)', zIndex: 3000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', backdropFilter: 'blur(12px)' }}
    >
      <motion.div 
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        className="card glass-panel" 
        style={{ 
          width: '100%', 
          maxWidth: '1200px', 
          height: '85vh', 
          display: 'flex', 
          flexDirection: 'column', 
          border: '1px solid var(--border-color)',
          borderRadius: '32px',
          overflow: 'hidden',
          boxShadow: '0 30px 60px rgba(0,0,0,0.6)'
        }}
      >
        {/* Header Section */}
        <div style={{ padding: '20px 30px', background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
             <div style={{ padding: '10px', borderRadius: '12px', background: 'var(--accent-translucent)', border: '1px solid var(--accent-ochre)' }}>
                <Sparkles size={22} color="var(--accent-ochre)" />
             </div>
             <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--accent-ochre)', margin: 0, letterSpacing: '1.5px' }}>{name.toUpperCase()}</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.6, fontSize: '0.75rem', marginTop: '2px' }}>
                  <Shield size={12} /> <span>IDENTITY PATTERN</span>
                </div>
             </div>
          </div>
          <button onClick={onClose} className="action-button" style={{ padding: '12px', borderRadius: '50%' }}>
            <X size={24} />
          </button>
        </div>
        
        {/* Split View Container */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          
          {/* Left Column: Editor (65%) */}
          <div style={{ flex: 0.65, display: 'flex', flexDirection: 'column', padding: '20px 30px', gap: '20px', borderRight: '1px solid var(--glass-border)' }}>
             <div style={{ padding: '15px', background: 'var(--nav-hover-bg)', borderRadius: '16px', borderLeft: '4px solid var(--accent-cyan)', display: 'flex', gap: '15px', alignItems: 'center' }}>
                <div style={{ padding: '8px', borderRadius: '50%', background: 'rgba(0, 109, 119, 0.1)', display: 'flex' }}>
                  <Activity size={18} color="var(--accent-cyan)" />
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', margin: 0, opacity: 0.8, lineHeight: '1.5' }}>
                  Operational essence synchronized. Changes locally redefine fundamental reasoning.
                </p>
             </div>
             
             <div style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column' }}>
                <div style={{ position: 'absolute', top: '12px', left: '12px', color: 'var(--accent-ochre)', opacity: 0.3, zIndex: 10 }}>
                  <Edit2 size={14} />
                </div>
                <textarea 
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  style={{ 
                    flex: 1, 
                    background: 'rgba(0,0,0,0.4)', 
                    color: 'var(--text-primary)', 
                    border: '1px solid var(--glass-border)', 
                    borderRadius: '20px', 
                    padding: '25px 20px 20px 35px', 
                    fontFamily: '"Fira Code", monospace', 
                    fontSize: '0.85rem', 
                    lineHeight: '1.6',
                    resize: 'none', 
                    outline: 'none',
                    boxShadow: 'inset 0 4px 20px rgba(0,0,0,0.4)'
                  }}
                  placeholder="Synchronizing with soul essence..."
                  disabled={loading}
                />
             </div>
          </div>

          {/* Right Column: AI Consultant (35%) */}
          <div style={{ flex: 0.35, display: 'flex', flexDirection: 'column', background: 'rgba(0,0,0,0.15)' }}>
             <div style={{ padding: '20px', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Activity size={14} color="var(--accent-ochre)" />
                <span style={{ fontSize: '0.75rem', fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '1px' }}>AI SOUL CONSULTANT</span>
             </div>
             
             <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
                {consultMessages.length === 0 && (
                  <div style={{ textAlign: 'center', padding: '40px 20px', opacity: 0.4 }}>
                    <Sparkles size={32} style={{ marginBottom: '10px', display: 'block', margin: '0 auto' }} />
                    <p style={{ fontSize: '0.8rem' }}>Ask the Identity Architect how to refine this expert's soul.</p>
                  </div>
                )}
                {consultMessages.map((msg, i) => (
                  <div key={i} style={{ 
                    padding: '12px 16px', 
                    borderRadius: '16px', 
                    background: msg.role === 'user' ? 'rgba(212, 163, 115, 0.1)' : 'rgba(255,255,255,0.03)',
                    borderLeft: msg.role === 'user' ? '3px solid var(--accent-ochre)' : 'none',
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: '90%'
                  }}>
                    <p style={{ margin: 0, fontSize: '0.8rem', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                  </div>
                ))}
                {consulting && <div style={{ opacity: 0.5, fontSize: '0.75rem', fontStyle: 'italic' }}>Architect is thinking...</div>}
             </div>

             <div style={{ padding: '20px', background: 'rgba(0,0,0,0.2)' }}>
                <div style={{ position: 'relative' }}>
                  <input 
                    type="text"
                    value={consultInput}
                    onChange={(e) => setConsultInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendConsult()}
                    placeholder="Refine behavior loop..."
                    style={{ 
                      width: '100%', 
                      background: 'var(--panel-bg)', 
                      border: '1px solid var(--glass-border)', 
                      borderRadius: '12px', 
                      padding: '12px 40px 12px 15px', 
                      fontSize: '0.8rem',
                      outline: 'none',
                      color: 'var(--text-primary)'
                    }}
                  />
                  <button 
                    onClick={handleSendConsult}
                    style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--accent-ochre)', cursor: 'pointer' }}
                  >
                    <Zap size={16} />
                  </button>
                </div>
             </div>
          </div>
        </div>

        {/* Action Row */}
        <div style={{ padding: '20px 40px 30px', display: 'flex', justifyContent: 'flex-end', gap: '15px', background: 'rgba(0,0,0,0.1)' }}>
           <button onClick={onClose} className="button-secondary" style={{ border: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>CANCEL RESONANCE</button>
           <button onClick={handleSave} className="button-primary" style={{ background: 'var(--accent-ochre)', color: 'var(--overlay-heavy-bg)', fontWeight: '900', boxShadow: '0 4px 20px var(--accent-glow)' }}>
             <Save size={18} /> EVOLVE IDENTITY
           </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

const GraphView = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [editingSoul, setEditingSoul] = useState(null);

  const fetchSwarm = useCallback(async () => {
    try {
      // 1. Fetch Experts for the base registry
      const expertsResp = await axios.get(`${API_BASE}/swarm/experts`);
      const experts = expertsResp.data.experts;
      
      // 2. Fetch the persisted Flow (positions and edges)
      const flowResp = await axios.get(`${API_BASE}/swarm/flow`);
      const flow = flowResp.data;

      if (flow.nodes && flow.nodes.length > 0) {
        // Use persisted nodes but refresh data callbacks
        const restoredNodes = flow.nodes.map(n => ({
          ...n,
          data: { 
            ...n.data, 
            onEdit: (name) => setEditingSoul(name), 
            onDelete: handleDeleteExpert 
          }
        }));
        setNodes(restoredNodes);
        setEdges(flow.edges || []);
      } else {
        // Fallback to initial row layout if no flow persisted
        const initialNodes = experts.map((name, i) => ({
          id: name,
          type: 'soul',
          position: { x: (i % 3) * 250, y: Math.floor(i / 3) * 200 },
          data: { label: name, onEdit: (n) => setEditingSoul(n), onDelete: handleDeleteExpert }
        }));
        setNodes(initialNodes);
      }
    } catch (e) {
      console.error("Failed to fetch swarm data", e);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    fetchSwarm();
  }, [fetchSwarm]);

  const handleSpawnExpert = async () => {
    const name = prompt("Name your new swarm expert (e.g. ResearcherV2):");
    if (!name) return;
    const role = prompt("Define their primary directive/role:", "Specialist agent for enhanced logic.");
    if (!role) return;

    try {
      await axios.post(`${API_BASE}/swarm/expert/spawn`, { name, role });
      fetchSwarm();
    } catch (e) {
      alert("Failed to spawn expert. Ensure name is unique.");
    }
  };

  const handleDeleteExpert = async (name) => {
    if (!window.confirm(`Dissolve ${name}? Their soul pattern will be permanently removed from the experts directory.`)) return;
    try {
      await axios.delete(`${API_BASE}/swarm/expert/${name}`);
      fetchSwarm();
    } catch (e) {
      alert("Failed to dissolve expert.");
    }
  };

  const handleTearAway = useCallback(({ text, title }) => {
    const id = `sticky-${Date.now()}`;
    const newNode = {
      id,
      type: 'sticky',
      position: { x: 100, y: 100 },
      data: { text, title }
    };
    setNodes((nds) => [...nds, newNode]);
  }, [setNodes]);

  const handleDeleteNode = useCallback((id) => {
    setNodes((nds) => nds.filter(node => node.id !== id));
  }, [setNodes]);

  const nodesWithCallbacks = nodes.map(node => {
    if (node.type === 'soul') {
        return { ...node, data: { ...node.data, onEdit: (n) => setEditingSoul(n), onDelete: handleDeleteExpert } };
    }
    return node;
  });

  const onConnect = useCallback((params) => {
    setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: 'var(--accent-cyan)', strokeWidth: 2 } }, eds));
  }, [setEdges]);

  // Persistence Hook: Save flow whenever nodes or edges change (debounced implicitly by reacting to state)
  useEffect(() => {
    if (nodes.length === 0) return;
    const timer = setTimeout(async () => {
      try {
        await axios.post(`${API_BASE}/swarm/flow`, { nodes, edges });
      } catch (e) {
        console.error("Failed to persist swarm flow", e);
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, [nodes, edges]);

  return (
    <div style={{ width: '100%', height: '100%', background: 'var(--bg-color)', borderRadius: '24px', border: '1px solid var(--border-color)', position: 'relative', overflow: 'hidden' }}>
      <AnimatePresence>
        {editingSoul && <SoulEditor name={editingSoul} onClose={() => setEditingSoul(null)} />}
      </AnimatePresence>
      <ReactFlow
        nodes={nodesWithCallbacks}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background variant="dots" gap={20} size={1} color="rgba(212, 163, 115, 0.05)" />
      </ReactFlow>
      <div style={{ position: 'absolute', top: '25px', left: '25px', zIndex: 1000, background: 'var(--panel-bg)', backdropFilter: 'blur(10px)', padding: '12px 20px', borderRadius: '16px', fontSize: '0.85rem', border: '1px solid var(--glass-border)', boxShadow: 'var(--card-shadow)', display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Activity size={18} color="var(--accent-cyan)" />
          <span style={{ fontWeight: '900', color: 'var(--text-primary)', letterSpacing: '1.5px' }}>SWARM EVOLUTION</span>
        </div>
        <div style={{ width: '1px', height: '20px', background: 'var(--border-color)' }}></div>
        <button 
          onClick={(e) => { e.stopPropagation(); handleSpawnExpert(); }}
          className="action-button"
          style={{ padding: '8px 16px', background: 'var(--accent-translucent)', border: '1px solid var(--accent-ochre)', color: 'var(--accent-ochre)' }}
        >
          <Plus size={16} /> <span>SPAWN EXPERT</span>
        </button>
      </div>
    </div>
  );
};

export default GraphView;
