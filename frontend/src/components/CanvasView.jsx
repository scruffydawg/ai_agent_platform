import React, { useEffect, useState } from 'react';
import { Tldraw, createShapeId } from '@tldraw/tldraw';
import '@tldraw/tldraw/tldraw.css';

const CanvasView = () => {
  const [editor, setEditor] = useState(null);

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

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
      <Tldraw 
        inferDarkMode 
        persistenceKey="ai-agent-platform-canvas"
        onMount={(editor) => setEditor(editor)}
      />
      <div style={{ position: 'absolute', top: '10px', left: '10px', zIndex: 1000, background: 'var(--panel-bg)', padding: '5px 10px', borderRadius: '4px', fontSize: '0.75rem', border: '1px solid var(--accent-cyan)', color: 'var(--accent-cyan)', pointerEvents: 'none' }}>
        TLDRAW CREATIVE CANVAS
      </div>
    </div>
  );
};

export default CanvasView;
