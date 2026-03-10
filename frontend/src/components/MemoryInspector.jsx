import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Layers, Tag, Shield, Info, Pin } from 'lucide-react';

const MemoryInspector = ({ contextPacket }) => {
  if (!contextPacket || contextPacket.length === 0) {
    return (
      <div className="card" style={{ padding: '40px', textAlign: 'center', opacity: 0.5 }}>
        <Brain size={48} style={{ marginBottom: '15px' }} />
        <p>No active context packet assembled.</p>
      </div>
    );
  }

  return (
    <div className="memory-inspector" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
        <Brain size={24} color="var(--accent-ochre)" />
        <h2 style={{ fontSize: '1.2rem', fontWeight: '900', margin: 0 }}>CONTEXT PACKET (GUIDE v3.0)</h2>
      </div>

      <p style={{ fontSize: '0.85rem', opacity: 0.7, marginBottom: '15px' }}>
        These are the specific memories the Memory Broker selected for the current agent reasoning step.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {contextPacket.map((item, idx) => {
          const isSystem = item.role === 'system';
          const isKnowledge = item.content.includes('[KNOWLEDGE]');
          const isWorking = item.content.includes('[WORKING]');
          const isResume = item.content.includes('[RESUME]');

          return (
            <motion.div 
              key={idx}
              initial={{ x: -10, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: idx * 0.05 }}
              style={{
                background: isSystem ? 'rgba(0,0,0,0.1)' : 'var(--nav-hover-bg)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                padding: '12px 16px',
                position: 'relative'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ 
                    fontSize: '0.65rem', 
                    fontWeight: '900', 
                    padding: '2px 6px', 
                    borderRadius: '4px',
                    background: isKnowledge ? 'var(--accent-cyan)' : isWorking ? 'var(--accent-ochre)' : 'var(--border-color)',
                    color: (isKnowledge || isWorking) ? 'var(--overlay-heavy-bg)' : 'var(--text-primary)'
                  }}>
                    {isKnowledge ? 'SEMANTIC' : isWorking ? 'WORKING' : isResume ? 'RESUME' : item.role.toUpperCase()}
                  </span>
                  <span style={{ fontSize: '0.7rem', opacity: 0.5 }}>{new Date().toLocaleTimeString()}</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                   <Pin size={12} style={{ opacity: 0.3, cursor: 'pointer' }} />
                   <Shield size={12} style={{ opacity: 0.3, cursor: 'pointer' }} />
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', lineHeight: '1.4', overflowWrap: 'anywhere' }}>
                {item.content.replace(/^\[.*?\]:\s?/, '')}
              </div>

              {/* Mock Metadata */}
              {(isKnowledge || isWorking) && (
                <div style={{ marginTop: '8px', display: 'flex', gap: '15px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px' }}>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.6rem', opacity: 0.6 }}>
                      <Tag size={10} /> CONFIDENCE: 1.0
                   </div>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.6rem', opacity: 0.6 }}>
                      <Info size={10} /> SOURCE: LOCAL
                   </div>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default MemoryInspector;
