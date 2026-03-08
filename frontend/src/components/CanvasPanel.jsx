import React, { useState, useEffect, Suspense } from 'react';
import { Tldraw } from '@tldraw/tldraw';
import '@tldraw/tldraw/tldraw.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  FileText, Code, Layout, Image as ImageIcon, Maximize2, Minimize2, 
  Eye, Edit3, PenTool, Eraser, Trash2, Download, Copy
} from 'lucide-react';

// Lazy load react-pdf to prevent SSR/startup issues if any
const Document = React.lazy(() => import('react-pdf').then(module => ({ default: module.Document })));
const Page = React.lazy(() => import('react-pdf').then(module => ({ default: module.Page })));

const CanvasPanel = ({ showFull, onToggleFull, isCollapsed, onRestore }) => {
  const [mode, setMode] = useState('MD'); // MD, CODE, PREVIEW, DOC
  const [content, setContent] = useState('');
  const [metadata, setMetadata] = useState({});
  const [numPages, setNumPages] = useState(null);
  const [isAnnotating, setIsAnnotating] = useState(false);

  const [isErasing, setIsErasing] = useState(false);

  // Common Tldraw configuration for simplified "annotation" feel
  const TldrawSimplified = ({ persistenceKey, hideUi = true, autoDraw = true, isErasing = false }) => {
    const [editor, setEditor] = useState(null);

    useEffect(() => {
      if (editor) {
        editor.setCurrentTool(isErasing ? 'eraser' : 'draw');
      }
    }, [editor, isErasing]);

    return (
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'all' }}>
        <Tldraw 
          inferDarkMode 
          persistenceKey={persistenceKey}
          hideUi={hideUi}
          onMount={(ed) => {
            setEditor(ed);
            if (autoDraw) ed.setCurrentTool(isErasing ? 'eraser' : 'draw');
          }}
          components={{
            Toolbar: () => null,
            Menu: () => null,
            NavigationPanel: () => null,
            PageMenu: () => null,
            MainMenu: () => null,
            ActionsMenu: () => null,
            StylePanel: () => null,
            HelpMenu: () => null,
            ZoomMenu: () => null,
          }}
        />
      </div>
    );
  };

  useEffect(() => {
    const handleCanvasPush = (e) => {
      const { type, payload, meta } = e.detail;
      if (type) setMode(type);
      if (payload !== undefined) setContent(payload);
      setMetadata(meta || {});
    };

    window.addEventListener('canvas-push', handleCanvasPush);
    return () => window.removeEventListener('canvas-push', handleCanvasPush);
  }, []);

  const handleCopy = () => {
    if (content) {
      navigator.clipboard.writeText(content);
    }
  };

  const handleDownload = (format) => {
    if (!content) return;
    let mimeType = 'text/plain';
    let fileExtension = 'txt';
    let data = content;

    if (format === 'json') {
      mimeType = 'application/json';
      fileExtension = 'json';
      try { data = JSON.stringify(JSON.parse(content), null, 2); } catch(e) {}
    } else if (format === 'pdf') {
      const printWindow = window.open('', '', 'width=800,height=600');
      printWindow.document.write('<pre style="white-space:pre-wrap;font-family:sans-serif;">' + content + '</pre>');
      printWindow.document.close();
      printWindow.focus();
      printWindow.print();
      printWindow.close();
      return;
    } else if (format === 'docx' || format === 'excel') {
      mimeType = format === 'excel' ? 'text/csv' : 'application/msword';
      fileExtension = format === 'excel' ? 'csv' : 'doc';
    }

    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `canvas_export.${fileExtension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };


  const renderContent = () => {
    switch (mode) {
      case 'MD':
        return (
          <div className="markdown-body" style={{ padding: '40px', height: '100%', overflowY: 'auto', background: 'var(--panel-bg)', color: 'var(--text-primary)' }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || ''}</ReactMarkdown>
          </div>
        );
      case 'CODE':
        return (
          <div style={{ height: '100%', overflow: 'hidden', background: '#1e1e1e' }}>
            <div style={{ padding: '10px 20px', background: '#2d2d2d', borderBottom: '1px solid #3d3d3d', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#aaa', fontFamily: 'monospace' }}>{metadata.filename || 'snippet.js'}</span>
            </div>
            <SyntaxHighlighter 
              language={metadata.language || 'javascript'} 
              style={vscDarkPlus}
              customStyle={{ margin: 0, height: 'calc(100% - 40px)', fontSize: '0.9rem' }}
            >
              {content || ''}
            </SyntaxHighlighter>
          </div>
        );
      case 'DOC':
        if (metadata.type === 'pdf') {
          return (
            <div style={{ height: '100%', overflowY: 'auto', display: 'flex', justifyContent: 'center', background: '#525659' }}>
              <Suspense fallback={<div style={{ color: 'white' }}>Loading PDF Viewer...</div>}>
                <Document
                  file={content}
                  onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                  loading={<div style={{ color: 'white' }}>Loading PDF...</div>}
                >
                  {Array.from(new Array(numPages || 0), (el, index) => (
                    <Page key={`page_${index + 1}`} pageNumber={index + 1} width={800} style={{ marginBottom: '20px' }} />
                  ))}
                </Document>
              </Suspense>
            </div>
          );
        }
        return <div style={{ padding: '40px', color: 'var(--text-primary)' }}>Document viewer for {metadata.type} coming soon.</div>;
      case 'PREVIEW':
        return (
          <iframe 
            srcDoc={content} 
            title="Preview" 
            style={{ width: '100%', height: '100%', border: 'none', background: 'white' }} 
          />
        );
      default:
        return (
          <div className="markdown-body" style={{ padding: '40px', height: '100%', overflowY: 'auto', background: 'var(--panel-bg)', color: 'var(--text-primary)' }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || ''}</ReactMarkdown>
          </div>
        );
    }
  };

  const renderAnnotationLayer = () => {
    if (!isAnnotating || mode === 'WHITEBOARD') return null;
    return (
      <div style={{ 
        position: 'absolute', 
        top: 0, 
        left: 0, 
        width: '100%', 
        height: '100%', 
        zIndex: 100,
        pointerEvents: 'all',
        background: 'rgba(212, 163, 115, 0.02)' // Extremely subtle tint to show pen mode active
      }}>
        <TldrawSimplified persistenceKey={`annotation-${mode}-${metadata.filename || 'overlay'}`} hideUi={true} isErasing={isErasing} />
      </div>
    );
  };

  const navItems = [
    { id: 'MD', icon: FileText, label: 'Document' },
    { id: 'CODE', icon: Code, label: 'Code' },
    { id: 'PREVIEW', icon: Eye, label: 'Preview' },
    { id: 'DOC', icon: ImageIcon, label: 'Files' },
  ];

  if (isCollapsed) {
    return (
      <div className="canvas-panel card" style={{ 
        display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden',
        border: '1px solid var(--border-color)', background: 'var(--header-bg)',
        alignItems: 'center', paddingTop: '20px', gap: '20px'
      }}>
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => { 
              setMode(item.id); 
              if (onRestore) onRestore(); 
            }}
            style={{
              background: mode === item.id ? 'var(--accent-ochre)' : 'transparent',
              color: mode === item.id ? 'black' : 'var(--text-primary)',
              border: 'none', borderRadius: '12px', padding: '12px', cursor: 'pointer',
              transition: 'all 0.2s', opacity: mode === item.id ? 1 : 0.6
            }}
            title={item.label}
          >
            <item.icon size={24} />
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="canvas-panel card" style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%', 
      overflow: 'hidden',
      border: '1px solid var(--border-color)',
      position: 'relative',
      background: 'var(--bg-color)'
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        padding: '10px 20px', 
        background: 'var(--nav-hover-bg)', 
        borderBottom: '1px solid var(--border-color)',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center', flexWrap: 'nowrap' }}>
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setMode(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 12px',
                borderRadius: '8px',
                border: 'none',
                background: mode === item.id ? 'var(--accent-ochre)' : 'transparent',
                color: mode === item.id ? 'var(--overlay-heavy-bg)' : 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: '700',
                transition: 'all 0.2s',
                opacity: mode === item.id ? 1 : 0.6,
                flexShrink: 0
              }}
            >
              <item.icon size={14} />
              {item.label}
            </button>
          ))}

          <div style={{ width: '1px', height: '15px', background: 'var(--border-color)', margin: '0 5px' }}></div>

          <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
            <button 
              onClick={() => {
                setIsAnnotating(!isAnnotating);
                if (isErasing) setIsErasing(false);
              }} 
              style={{ 
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '8px',
                border: `1px solid ${isAnnotating && !isErasing ? 'var(--accent-ochre)' : 'transparent'}`,
                background: isAnnotating && !isErasing ? 'rgba(212, 163, 115, 0.1)' : 'transparent',
                color: isAnnotating && !isErasing ? 'var(--accent-ochre)' : 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: '700',
                transition: 'all 0.2s',
                opacity: 0.8
              }}
              title="Toggle Annotation Pen"
            >
              <PenTool size={14} />
              ANNOTATE
            </button>
            {isAnnotating && (
              <button 
                onClick={() => setIsErasing(!isErasing)} 
                style={{ 
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '8px',
                  border: `1px solid ${isErasing ? 'var(--accent-red)' : 'transparent'}`,
                  background: isErasing ? 'rgba(255, 68, 68, 0.1)' : 'transparent',
                  color: isErasing ? 'var(--accent-red)' : 'var(--text-primary)',
                  cursor: 'pointer',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  transition: 'all 0.2s',
                  opacity: 0.8
                }}
                title="Toggle Eraser"
              >
                <Eraser size={14} /> ERASE
              </button>
            )}
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', paddingRight: '120px' }}>
             {content && (
               <div style={{ display: 'flex', gap: '6px', marginRight: '15px' }}>
                 <button onClick={handleCopy} title="Copy Content" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', cursor: 'pointer', padding: '4px 8px', borderRadius: '6px', fontSize: '0.65rem', fontWeight: 'bold' }}>
                   <Copy size={12} /> COPY
                 </button>
                 <button onClick={() => handleDownload('pdf')} title="Print / PDF" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', cursor: 'pointer', padding: '4px 8px', borderRadius: '6px', fontSize: '0.65rem', fontWeight: 'bold' }}>
                   <Download size={12} /> PDF
                 </button>
                 <button onClick={() => handleDownload('json')} title="Download JSON" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', cursor: 'pointer', padding: '4px 8px', borderRadius: '6px', fontSize: '0.65rem', fontWeight: 'bold' }}>
                   <Download size={12} /> JSON
                 </button>
                 <button onClick={() => handleDownload('docx')} title="Download DOCX" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', cursor: 'pointer', padding: '4px 8px', borderRadius: '6px', fontSize: '0.65rem', fontWeight: 'bold' }}>
                   <Download size={12} /> DOCX
                 </button>
                 <button onClick={() => handleDownload('excel')} title="Download Excel" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', cursor: 'pointer', padding: '4px 8px', borderRadius: '6px', fontSize: '0.65rem', fontWeight: 'bold' }}>
                   <Download size={12} /> CSV
                 </button>
               </div>
             )}
             <button onClick={onToggleFull} style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', opacity: 0.6 }}>
                 {showFull ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
             </button>
        </div>
      </div>

      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {renderContent()}
        {renderAnnotationLayer()}
      </div>

      <div style={{ 
        position: 'absolute', 
        bottom: '20px', 
        right: '24px', 
        zIndex: 5, 
        padding: '4px 12px', 
        borderRadius: '20px', 
        background: 'var(--overlay-heavy-bg)', 
        color: 'var(--accent-ochre)', 
        fontSize: '0.65rem', 
        fontWeight: '900', 
        border: '1px solid var(--accent-ochre)',
        letterSpacing: '1px',
        pointerEvents: 'none',
        opacity: 0.8
      }}>
        CANVAS // {mode}
      </div>
    </div>
  );
};

export default CanvasPanel;
