import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, X, RotateCcw } from 'lucide-react';

const ResumePanel = ({ resumeData, onResume, onDiscard }) => {
  if (!resumeData) return null;

  return (
    <motion.div 
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: -50, opacity: 0 }}
      style={{
        background: 'rgba(212, 163, 115, 0.1)',
        backdropFilter: 'blur(10px)',
        border: '1px solid var(--accent-ochre)',
        borderRadius: '16px',
        padding: '16px 20px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
        gap: '20px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
        <div style={{ 
          background: 'var(--accent-ochre)', 
          padding: '10px', 
          borderRadius: '12px',
          color: 'var(--overlay-heavy-bg)'
        }}>
          <RotateCcw size={20} />
        </div>
        <div>
          <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-ochre)', letterSpacing: '1px' }}>
            INTERRUPTION DETECTED
          </h4>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', opacity: 0.8 }}>
            Would you like to resume: <span style={{ fontWeight: '600' }}>"{resumeData.content}"</span>?
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button 
          onClick={onResume}
          style={{
            background: 'var(--accent-ochre)',
            color: 'var(--overlay-heavy-bg)',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '10px',
            fontSize: '0.8rem',
            fontWeight: '800',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Play size={14} /> RESUME
        </button>
        <button 
          onClick={onDiscard}
          style={{
            background: 'transparent',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
            padding: '8px 12px',
            borderRadius: '10px',
            fontSize: '0.8rem',
            cursor: 'pointer'
          }}
        >
          <X size={14} />
        </button>
      </div>
    </motion.div>
  );
};

export default ResumePanel;
