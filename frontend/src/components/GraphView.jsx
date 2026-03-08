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
import { Edit2, Plus, X, Save, Zap } from 'lucide-react';
import 'reactflow/dist/style.css';

import { API_BASE } from '../api.js';

const SoulNode = ({ data, id }) => (
  <div className="card" style={{ 
    padding: '15px', 
    background: 'var(--panel-bg)', 
    border: '2px solid var(--accent-ochre)', 
    borderRadius: '12px', 
    width: '200px',
    position: 'relative',
    boxShadow: '0 4px 20px rgba(212, 163, 115, 0.15)'
  }}>
    <Handle type="target" position={Position.Top} style={{ background: 'var(--accent-cyan)' }} />
    <Handle type="source" position={Position.Bottom} style={{ background: 'var(--accent-cyan)' }} />
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
      <Zap size={16} color="var(--accent-ochre)" />
      <span style={{ fontWeight: 'bold', fontSize: '0.9rem', color: 'var(--text-primary)' }}>{data.label}</span>
      <button 
        onClick={(e) => { e.stopPropagation(); data.onDelete(data.label); }}
        style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'var(--accent-red)', cursor: 'pointer', padding: '2px' }}
        title="Dissolve Expert"
      >
        <X size={14} />
      </button>
    </div>
    <p style={{ fontSize: '0.7rem', opacity: 0.85, marginBottom: '10px', color: 'var(--text-primary)' }}>{data.role || 'Swarm Expert'}</p>
    <button 
      onClick={() => data.onEdit(data.label)}
      className="button-secondary" 
      style={{ width: '100%', fontSize: '0.65rem', padding: '6px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}
    >
      <Zap size={12} /> REVEAL SOUL
    </button>
  </div>
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

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'var(--overlay-bg)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px', backdropFilter: 'blur(8px)' }}>
      <div className="card glass-effect" style={{ width: '100%', maxWidth: '900px', height: '85vh', display: 'flex', flexDirection: 'column', gap: '20px', border: '1px solid var(--accent-ochre)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
             <Zap size={24} color="var(--accent-ochre)" />
             <h2 style={{ color: 'var(--accent-ochre)', margin: 0 }}>SOUL OF {name.toUpperCase()}</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}><X size={24} /></button>
        </div>
        
        <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: '15px' }}>
           <div style={{ padding: '15px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: '4px solid var(--accent-cyan)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>IDENTITY DEEP-DIVE</span>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', margin: 0, opacity: 0.9 }}>This agent operates under the collective moral compass defined in SOUL.md, with the following specialized architecture.</p>
           </div>
           
           <textarea 
             value={content}
             onChange={(e) => setContent(e.target.value)}
             style={{ flex: 1, background: 'var(--bg-color)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '20px', fontFamily: 'monospace', fontSize: '0.9rem', resize: 'none', boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.2)' }}
             placeholder="Synchronizing with soul essence..."
             disabled={loading}
           />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '15px', paddingTop: '10px' }}>
           <button onClick={onClose} className="button-secondary">CLOSE RESONANCE</button>
           <button onClick={handleSave} className="button-primary" style={{ background: 'var(--accent-ochre)', color: 'white' }}>
             <Save size={18} /> EVOLVE SOUL
           </button>
        </div>
      </div>
    </div>
  );
};

const GraphView = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [editingSoul, setEditingSoul] = useState(null);

  const fetchSwarm = useCallback(async () => {
    try {
      const resp = await axios.get(`${API_BASE}/swarm/experts`);
      const experts = resp.data.experts;
      const newNodes = experts.map((name, i) => ({
        id: name,
        type: 'soul',
        position: { x: (i % 3) * 250, y: Math.floor(i / 3) * 200 },
        data: { label: name, onEdit: (n) => setEditingSoul(n), onDelete: handleDeleteExpert }
      }));
      setNodes(newNodes);

      const computedEdges = [];
      for (let i = 0; i < experts.length - 1; i++) {
        computedEdges.push({
          id: `e-${experts[i]}-${experts[i+1]}`,
          source: experts[i],
          target: experts[i+1],
          animated: true,
          type: 'smoothstep',
          style: { stroke: 'var(--accent-cyan)', strokeWidth: 2 }
        });
      }
      setEdges(computedEdges);
    } catch (e) {
      console.error("Failed to fetch experts", e);
    }
  }, [setNodes]);

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

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  return (
    <div style={{ width: '100%', height: '100%', background: 'var(--bg-color)', borderRadius: '12px', border: '1px solid var(--border-color)', position: 'relative' }}>
      {editingSoul && <SoulEditor name={editingSoul} onClose={() => setEditingSoul(null)} />}
      <ReactFlow
        nodes={nodesWithCallbacks}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background variant="dots" gap={12} size={1} color="var(--border-color)" />
      </ReactFlow>
      <div style={{ position: 'absolute', top: '20px', left: '20px', zIndex: 1000, background: 'var(--panel-bg)', padding: '10px 15px', borderRadius: '12px', fontSize: '0.8rem', border: '1px solid var(--accent-cyan)', boxShadow: 'var(--card-shadow)', display: 'flex', alignItems: 'center', gap: '15px' }}>
        <span style={{ fontWeight: '800', color: 'var(--accent-cyan)', letterSpacing: '1px' }}>SWARM LOGIC</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={(e) => { e.stopPropagation(); handleSpawnExpert(); }}
            className="button-secondary"
            style={{ fontSize: '0.75rem', padding: '6px 14px', borderRadius: '8px', border: '1px solid var(--accent-ochre)', color: 'var(--accent-ochre)' }}
          >
            + EXPERT
          </button>
        </div>
      </div>
    </div>
  );
};

export default GraphView;
