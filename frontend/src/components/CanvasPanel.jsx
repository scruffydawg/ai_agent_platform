import React, { useState, useEffect, Suspense, useRef } from 'react';
import { Tldraw } from '@tldraw/tldraw';
import '@tldraw/tldraw/tldraw.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  FileText, Code, Layout, Image as ImageIcon, Maximize2, Minimize2, 
  Eye, Edit3, PenTool, Eraser, Trash2, Download, Copy, History, Clock
} from 'lucide-react';

// Lazy load react-pdf to prevent SSR/startup issues if any
const Document = React.lazy(() => import('react-pdf').then(module => ({ default: module.Document })));
const Page = React.lazy(() => import('react-pdf').then(module => ({ default: module.Page })));

const CanvasPanel = ({ showFull, onToggleFull, isCollapsed, onRestore, isSmall }) => {
  const [mode, setMode] = useState('MD'); // MD, CODE, PREVIEW, DOC
  const [content, setContent] = useState('');
  const [metadata, setMetadata] = useState({});
  const [numPages, setNumPages] = useState(null);
  const [isAnnotating, setIsAnnotating] = useState(false);
  const [isErasing, setIsErasing] = useState(false);
  
  // Artifact History State
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const historyRef = useRef(null);

  // Close history dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (historyRef.current && !historyRef.current.contains(event.target)) {
        setShowHistory(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
      const { mode: pushedMode, type, content: pushedContent, payload, metadata: pushedMetadata, meta } = e.detail;
      
      const finalMode = pushedMode || type;
      if (finalMode && finalMode !== 'canvas_push') setMode(finalMode);
      
      const finalContent = pushedContent !== undefined ? pushedContent : payload;
      if (finalContent !== undefined) setContent(finalContent);
      
      const finalMeta = pushedMetadata || meta || {};
      setMetadata(finalMeta);
      
      if (finalMode === 'MANIFESTATION') {
        // Manifestation payload is a UIScreen object
        // We'll set the content to the UIScreen object directly if it matches the schema
        if (payload?.components || pushedContent?.components) {
          setContent(payload || pushedContent);
        }
      }
      
      // Save to history
      if (finalContent || finalMeta.filename) {
        setHistory(prev => {
          const newItem = {
            id: Date.now(),
            time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
            mode: finalMode || 'MD',
            content: finalContent,
            metadata: finalMeta,
            filename: finalMeta.filename || `${finalMode} Artifact`
          };
          // Don't duplicate if it's the exact same content consecutively
          if (prev.length > 0 && prev[0].content === finalContent) return prev;
          return [newItem, ...prev].slice(0, 50); // Keep last 50
        });
      }
    };

    window.addEventListener('canvas-push', handleCanvasPush);
    return () => window.removeEventListener('canvas-push', handleCanvasPush);
  }, []);

  const restoreHistoryItem = (item) => {
    setMode(item.mode);
    setContent(item.content);
    setMetadata(item.metadata);
    setShowHistory(false);
  };

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
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{typeof content === 'string' ? content : JSON.stringify(content, null, 2)}</ReactMarkdown>
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
        if (metadata.saved_path?.endsWith('pdf') || metadata.type === 'pdf') {
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
        return <div style={{ padding: '40px', color: 'var(--text-primary)' }}>Document viewer for {metadata.filename || 'this file'} coming soon.</div>;
      case 'PREVIEW':
        return (
          <iframe 
            srcDoc={content} 
            title="Preview" 
            style={{ width: '100%', height: '100%', border: 'none', background: 'white' }} 
          />
        );
      case 'MANIFESTATION':
        return (
          <div style={{ 
            height: '100%', overflowY: 'auto', padding: '20px', 
            background: 'var(--panel-bg)', display: 'flex', flexDirection: 'column', gap: '20px' 
          }}>
            <h2 style={{ color: 'var(--accent-ochre)', marginBottom: '10px' }}>{content?.title || 'Agent Manifestation'}</h2>
            <div style={{ 
              display: content?.layout === 'bento' ? 'grid' : 'flex',
              gridTemplateColumns: content?.layout === 'bento' ? 'repeat(auto-fill, minmax(300px, 1fr))' : 'none',
              flexDirection: content?.layout === 'bento' ? 'row' : 'column',
              gap: '15px'
            }}>
              {content?.components?.map(comp => (
                <div key={comp.id} className="card" style={{ 
                  padding: '15px', background: 'var(--bg-color)', border: '1px solid var(--border-color)',
                  borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                }}>
                  <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {comp.type === 'list' && <FileText size={14} />}
                    {comp.label}
                  </h3>
                  {comp.type === 'list' && Array.isArray(comp.content) ? (
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                      {comp.content.map((item, idx) => <li key={idx} style={{ padding: '4px 0', borderBottom: '1px solid var(--border-color)', fontSize: '0.9rem' }}>{String(item)}</li>)}
                    </ul>
                  ) : comp.type === 'json' ? (
                    <pre style={{ fontSize: '0.8rem', opacity: 0.8, overflowX: 'auto' }}>{JSON.stringify(comp.content, null, 2)}</pre>
                  ) : (
                    <div style={{ fontSize: '1rem', lineHeight: 1.5 }}>{String(comp.content)}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      default:
        return (
          <div className="markdown-body" style={{ padding: '40px', height: '100%', overflowY: 'auto', background: 'var(--panel-bg)', color: 'var(--text-primary)' }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{typeof content === 'string' ? content : JSON.stringify(content, null, 2)}</ReactMarkdown>
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

  if (isCollapsed) {
    return (
      <div className="canvas-panel card" style={{ 
        display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden',
        border: '1px solid var(--border-color)', background: 'var(--header-bg)',
        alignItems: 'center', justifyContent: 'center', paddingTop: '10px', gap: '20px'
      }}>
        <button
          onClick={() => { if (onRestore) onRestore(); }}
          style={{
            background: 'var(--accent-ochre)',
            color: 'black',
            border: 'none', borderRadius: '12px', padding: '12px', cursor: 'pointer',
            transition: 'all 0.2s', opacity: 1, boxShadow: '0 4px 12px rgba(212, 163, 115, 0.3)'
          }}
          title="Open Artifact Canvas"
        >
          <Layout size={24} />
        </button>
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
        padding: isSmall ? '10px 10px' : '10px 20px', 
        background: 'var(--nav-hover-bg)', 
        borderBottom: '1px solid var(--border-color)',
        zIndex: 10,
        minHeight: '52px'
      }}>
        <div style={{ display: 'flex', gap: isSmall ? '8px' : '15px', alignItems: 'center', flexWrap: 'nowrap', height: '100%' }}>
          
          {/* History Dropdown */}
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }} ref={historyRef}>
            <button 
              onClick={() => setShowHistory(!showHistory)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', height: '32px',
                background: showHistory ? 'var(--accent-ochre)' : 'transparent',
                color: showHistory ? 'var(--bg-color)' : 'var(--text-primary)',
                border: 'none', padding: isSmall ? '0 8px' : '0 12px', borderRadius: '6px',
                cursor: 'pointer', transition: 'all 0.2s', opacity: showHistory ? 1 : 0.7
              }}
              title="Artifact History"
            >
              <History size={16} /> 
              {!isSmall && <span style={{ fontSize: '0.8rem', fontWeight: 'bold', lineHeight: 1, paddingTop: '1px' }}>Artifacts</span>}
            </button>
            
            {showHistory && (
              <div style={{
                position: 'absolute', top: '100%', left: 0, marginTop: '8px',
                width: '300px', maxHeight: '400px', overflowY: 'auto',
                background: 'var(--panel-bg)', border: '1px solid var(--border-color)',
                borderRadius: '8px', boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                zIndex: 100, padding: '8px', display: 'flex', flexDirection: 'column', gap: '4px'
              }}>
                <div style={{ padding: '8px', fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-color)', marginBottom: '4px' }}>
                  PREVIOUS ARTIFACTS
                </div>
                {history.length === 0 ? (
                  <div style={{ padding: '12px', fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'center' }}>No history yet.</div>
                ) : (
                  history.map(item => (
                    <button 
                      key={item.id}
                      onClick={() => restoreHistoryItem(item)}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '10px', background: 'transparent', border: 'none',
                        color: 'var(--text-primary)', textAlign: 'left', borderRadius: '6px',
                        cursor: 'pointer', outline: 'none'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.background = 'var(--nav-hover-bg)'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <div style={{ flex: 1, overflow: 'hidden' }}>
                        <div style={{ fontSize: '0.85rem', fontWeight: 'bold', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.filename}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span style={{ padding: '2px 6px', background: 'var(--bg-color)', borderRadius: '4px' }}>{item.mode}</span> 
                        </div>
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={10} /> {item.time}
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
          
          <div style={{ width: '1px', height: '15px', background: 'var(--border-color)', margin: '0 5px' }}></div>

          <div style={{ width: '1px', height: '15px', background: 'var(--border-color)', margin: '0 5px' }}></div>

          <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexShrink: 0 }}>
            <button 
              onClick={() => {
                setIsAnnotating(!isAnnotating);
                if (isErasing) setIsErasing(false);
              }} 
              style={{ 
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                border: `1px solid ${isAnnotating && !isErasing ? 'var(--accent-ochre)' : 'transparent'}`,
                background: isAnnotating && !isErasing ? 'rgba(212, 163, 115, 0.1)' : 'transparent',
                color: isAnnotating && !isErasing ? 'var(--accent-ochre)' : 'var(--text-primary)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                opacity: 0.8
              }}
              title={isAnnotating && !isErasing ? 'Annotation Active' : 'Toggle Annotation Pen'}
            >
              <PenTool size={16} />
            </button>
            {isAnnotating && (
              <button 
                onClick={() => setIsErasing(!isErasing)} 
                style={{ 
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '32px',
                  height: '32px',
                  borderRadius: '6px',
                  border: `1px solid ${isErasing ? 'var(--accent-red)' : 'transparent'}`,
                  background: isErasing ? 'rgba(255, 68, 68, 0.1)' : 'transparent',
                  color: isErasing ? 'var(--accent-red)' : 'var(--text-primary)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  opacity: 0.8
                }}
                title={isErasing ? 'Eraser Active' : 'Toggle Eraser'}
              >
                <Eraser size={16} />
              </button>
            )}
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: isSmall ? '4px' : '8px', alignItems: 'center', flexShrink: 0, height: '100%' }}>
             {content && (
               <div style={{ display: 'flex', gap: '4px', background: 'var(--panel-bg)', padding: '2px', borderRadius: '8px', border: '1px solid var(--border-color)', alignItems: 'center' }}>
                 <button onClick={handleCopy} title="Copy Content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '26px', height: '26px', background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', borderRadius: '6px', opacity: 0.7, transition: 'all 0.2s' }} onMouseOver={(e) => e.currentTarget.style.background = 'var(--nav-hover-bg)'} onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}>
                   <Copy size={14} />
                 </button>
                 <button onClick={() => handleDownload('pdf')} title="Export PDF" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '26px', height: '26px', background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', borderRadius: '6px', opacity: 0.7, transition: 'all 0.2s' }} onMouseOver={(e) => e.currentTarget.style.background = 'var(--nav-hover-bg)'} onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}>
                   <Download size={14} />
                 </button>
               </div>
             )}



             <button onClick={onToggleFull} title={showFull ? "Minimize" : "Maximize"} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '32px', height: '32px', background: 'var(--nav-hover-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)', cursor: 'pointer', transition: 'all 0.2s', opacity: 0.8 }}>
                 {showFull ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
             </button>
        </div>
      </div>

      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {renderContent()}
        {renderAnnotationLayer()}
      </div>
    </div>
  );
};

export default CanvasPanel;
