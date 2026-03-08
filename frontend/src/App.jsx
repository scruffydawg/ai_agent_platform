import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Terminal, Brain, Mic, Volume2, Power, Layout, Clock, Activity,
  Send, MessageSquare, Network, Settings, HelpCircle, Monitor, Camera, Shield, Search, Hammer, ExternalLink, Sun, Moon, Plus, Puzzle, Maximize2, Minimize2, PanelRight, Edit3, History
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion, AnimatePresence } from 'framer-motion';
import CanvasPanel from './components/CanvasPanel';
import GraphView from './components/GraphView';
import SettingsView from './components/SettingsView';
import HelpView from './components/HelpView';
import SystemsDashboard from './components/SwarmView';
import SkillForge from './components/SkillForge';
import ToolRegistry from './components/ToolRegistry';

import { API_BASE, WS_BASE } from './api.js';

const App = () => {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'GUIDE ONLINE. The Flute Path is clear. How may I navigate for you?', id: 1 }
  ]);
  const [input, setInput] = useState('');
  const [activeView, setActiveView] = useState('chat');
  const [agentStatus, setAgentStatus] = useState('idle');
  const [isHalted, setIsHalted] = useState(false);
  const [helpTopic, setHelpTopic] = useState(null);
  const [showPrivacyModal, setShowPrivacyModal] = useState(null); // 'screenshot' or 'webcam'
  const [visionPreview, setVisionPreview] = useState(null);
  const [pendingFilename, setPendingFilename] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessionSearch, setSessionSearch] = useState('');
  const [showFullSessions, setShowFullSessions] = useState(true);
  const [showDashboardOverlay, setShowDashboardOverlay] = useState(false);
  const [showCanvas, setShowCanvas] = useState(false);
  const [showSessionsPane, setShowSessionsPane] = useState(false);
  const [canvasSplitIndex, setCanvasSplitIndex] = useState(0);
  const [showSidebar, setShowSidebar] = useState(true);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const resp = await axios.get(`${API_BASE}/sessions`);
      const sessionsArr = resp.data.sessions || [];
      setSessions(sessionsArr);
      return sessionsArr;
    } catch (e) {
      console.error("Failed to fetch sessions", e);
      return [];
    }
  };

  // Fetch Sessions and Config on Mount
  useEffect(() => {
    const init = async () => {
      const sessionsArr = await fetchSessions();
      if (sessionsArr.length > 0) {
        const firstSession = sessionsArr[0];
        const idToLoad = (typeof firstSession === 'string') ? firstSession : firstSession.id;
        if (idToLoad) loadSession(idToLoad);
        else handleNewSession();
      } else {
        handleNewSession();
      }
    };
    init();
  }, []);

  const handleNewSession = async () => {
    try {
       const resp = await axios.post(`${API_BASE}/sessions/new`);
       const newId = resp.data.session_id;
       const newSession = { id: newId, title: "New Session", created_at: Date.now() / 1000, last_updated: Date.now() / 1000 };
       setCurrentSessionId(newId);
       setMessages([{ role: 'assistant', content: 'NEW SESSION INITIALIZED. I am your Guide. How shall we proceed?', id: Date.now() }]);
       setSessions(prev => [newSession, ...prev]);
       setActiveView("chat");
    } catch (e) {
       console.error("Failed to create new session", e);
    }
  };

  const loadSession = async (id) => {
    if (!id) {
      console.warn("Attempted to load session with undefined ID");
      return;
    }
    try {
      const resp = await axios.get(`${API_BASE}/sessions/${id}`);
      setMessages(resp.data.messages.length > 0 ? resp.data.messages : [{ role: 'assistant', content: 'SESSION RESTORED.', id: Date.now() }]);
      setCurrentSessionId(id);
      setActiveView('chat');
    } catch (e) {
      console.error("Failed to load session", e);
    }
  };

  const persistMessage = async (sessionId, role, content) => {
    if (!sessionId) return;
    try {
      const resp = await axios.post(`${API_BASE}/sessions/${sessionId}/message`, { role, content });
      // If the backend renamed the session (autotitling), update local ID
      if (resp.data.session_id && resp.data.session_id !== sessionId) {
        console.log(`Session renamed: ${sessionId} -> ${resp.data.session_id}`);
        setCurrentSessionId(resp.data.session_id);
        fetchSessions(); // Refresh sidebar to show new title
      }
    } catch (e) {
      console.error("Failed to persist message", e);
    }
  };

  // Sync with Backend Heartbeat and Events
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/stream`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'heartbeat') {
        setIsHalted(data.halted);
      } else if (data.type === 'canvas_push') {
        // Broadcast custom event for CanvasPanel to pick up
        const canvasEvent = new CustomEvent('canvas-push', { 
          detail: { type: data.mode, payload: data.content, meta: data.metadata } 
        });
        window.dispatchEvent(canvasEvent);
        
        // Auto-open canvas
        setShowCanvas(true);
        setCanvasSplitIndex(3); // 25/75 split
      }
    };
    return () => ws.close();
  }, []);

  const handleRun = async () => {
    if (!input.trim() || agentStatus === 'thinking') return;
    
    setAgentStatus('thinking');
    const userMsg = { role: 'user', content: input, id: Date.now() };
    const currentInput = input;
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');

    // Persist User Message
    persistMessage(currentSessionId, 'user', currentInput);

    let assistantReply = '';
    const assistantMsgId = Date.now() + 1;
    
    try {
      const history = newMessages.slice(-20).map(m => ({ role: m.role, content: m.content }));
      
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: currentInput,
          history: history.slice(0, -1)
        })
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      // Add placeholder assistant message
      setMessages(prev => [...prev, { role: 'assistant', content: '', id: assistantMsgId }]);

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep partial line in buffer
        
        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            try {
              const cleanedLine = line.trim().slice(6);
              if (!cleanedLine) continue;
              const data = JSON.parse(cleanedLine);
              if (data.content) {
                assistantReply += data.content;
                setMessages(prev => prev.map(m => 
                  m.id === assistantMsgId ? { ...m, content: assistantReply } : m
                ));
              }
              if (data.error) throw new Error(data.error);
            } catch (e) {
              console.error("Error parsing SSE chunk", e, "Line:", line);
            }
          }
        }
      }

      persistMessage(currentSessionId, 'assistant', assistantReply);
      setAgentStatus('idle');

      // Refresh sessions
      const sResp = await axios.get(`${API_BASE}/sessions`);
      setSessions(sResp.data.sessions);
    } catch (error) {
      console.error('Chat error:', error);
      const errMsg = { 
        role: 'assistant', 
        content: `⚠️ Error: ${error.message || 'Could not reach the model.'}`, 
        id: Date.now() + 2 
      };
      setMessages(prev => [...prev.filter(m => m.id !== assistantMsgId), errMsg]);
      setAgentStatus('error');
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const triggerKillSwitch = async () => {
    await axios.post(`${API_BASE}/kill`);
    setIsHalted(true);
  };

  const handleOpenHelp = (topic) => {
    setHelpTopic(topic);
    setActiveView('help');
  };

  const triggerVision = async (type, forced = false) => {
    try {
      if (type === 'screenshot' && !forced) {
        // Initial capture attempt (silent scan)
        const resp = await axios.post(`${API_BASE}/vision/screenshot?confirm=true`);
        if (resp.data.status === 'requires_auth') {
          setVisionPreview(resp.data.preview);
          setPendingFilename(resp.data.filename);
          setShowPrivacyModal('screenshot');
        } else {
          alert(`Captured: ${resp.data.path}`);
        }
      } else if (type === 'screenshot' && forced) {
        // Finalize buffered capture
        await axios.post(`${API_BASE}/vision/confirm?filename=${pendingFilename}`);
        alert("Capture authorized and saved.");
        setShowPrivacyModal(null);
        setVisionPreview(null);
      } else if (type === 'webcam') {
        // Webcam still requires pre-auth
        const resp = await axios.post(`${API_BASE}/vision/webcam?confirm=true`);
        alert(`Webcam saved: ${resp.data.path}`);
        setShowPrivacyModal(null);
      }
    } catch (e) {
      alert("Vision action failed.");
      setShowPrivacyModal(null);
    }
  };

  const handlePushToCanvas = (type, payload, meta = {}) => {
    if (!showCanvas) {
      setShowCanvas(true);
      setCanvasSplitIndex(3); // Auto-pop at 25/75 (Chat: 25%, Canvas: 75%)
    }
    const event = new CustomEvent('canvas-push', { 
      detail: { type, payload, meta } 
    });
    window.dispatchEvent(event);
  };

  const handleTearAwayToCanvas = (content) => {
    handlePushToCanvas('WHITEBOARD', content);
    console.log("Taring away to whiteboard:", content);
  };

  const PrivacyModal = ({ type, onClose }) => (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'var(--overlay-bg)', backdropFilter: 'blur(10px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 3000 }}>
       <div className="card" style={{ maxWidth: '600px', border: '4px solid var(--accent-red)', padding: '40px', textAlign: 'center', boxShadow: 'var(--card-shadow)' }}>
          <Shield size={64} color="var(--accent-red)" style={{ marginBottom: '20px' }} />
          <h2 style={{ fontSize: '2rem', color: 'var(--accent-red)', fontWeight: '900' }}>PRIVACY ALERT</h2>
          
          {visionPreview ? (
            <div style={{ margin: '20px 0', border: '2px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden' }}>
              <img src={`data:image/png;base64,${visionPreview}`} style={{ width: '100%', display: 'block' }} alt="Privacy Sensitive Preview" />
              <div style={{ background: 'var(--accent-translucent)', padding: '10px', fontSize: '0.8rem', color: 'var(--accent-red)' }}>
                SENSITIVE CONTENT DETECTED
              </div>
            </div>
          ) : (
            <p style={{ fontSize: '1.2rem', margin: '20px 0', opacity: 0.9, color: 'var(--text-primary)' }}>
              The AI is requesting access to your <strong>{type.toUpperCase()}</strong>.
            </p>
          )}

          <p style={{ opacity: 0.7, marginBottom: '20px', color: 'var(--text-primary)' }}>
            Authorize to store this capture in your standard AI storage schema.
          </p>

          <div style={{ display: 'flex', gap: '20px', justifyContent: 'center' }}>
             <button onClick={() => triggerVision(type, !!visionPreview)} className="button-primary" style={{ background: 'var(--accent-green)', color: 'black', fontWeight: 'bold' }}>AUTHORIZE</button>
             <button onClick={() => { onClose(); setVisionPreview(null); }} className="button-secondary">DENY & DISCARD</button>
          </div>
       </div>
    </div>
  );

  return (
    <div className={`app-container ${theme === 'dark' ? 'neon-dark' : 'vibrant-light'}`}>
      {showPrivacyModal && <PrivacyModal type={showPrivacyModal} onClose={() => setShowPrivacyModal(null)} />}
      
      {/* Sidebar Navigation */}
      <div className={`sidebar ${!showSidebar ? 'collapsed' : ''}`} style={{ width: showSidebar ? '280px' : '80px', transition: 'width 0.3s ease', zIndex: 50 }}>
        <button 
          onClick={() => setShowSidebar(!showSidebar)}
          style={{ position: 'absolute', top: '20px', right: '-15px', zIndex: 100, background: 'var(--accent-ochre)', border: 'none', borderRadius: '50%', width: '30px', height: '30px', color: 'black', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 0 10px rgba(0,0,0,0.3)' }}
        >
          {showSidebar ? <PanelRight size={16} style={{ transform: 'rotate(180deg)' }} /> : <PanelRight size={16} />}
        </button>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', marginBottom: '40px', gap: '10px' }}>
          <img 
            src="/ehecatl.png" 
            style={{ width: showSidebar ? '100px' : '50px', height: showSidebar ? '100px' : '50px', borderRadius: '50%', border: '2px solid var(--accent-ochre)', boxShadow: '0 0 15px rgba(212, 163, 115, 0.3)', transition: 'all 0.3s ease' }}
            alt="Guide Mascot"
          />
          {showSidebar && <h2 style={{ fontSize: '2.4rem', margin: 0, fontWeight: '900', color: 'var(--accent-ochre)', letterSpacing: '4px' }}>GUIDE</h2>}
        </div>

        <button 
          onClick={handleNewSession}
          style={{ 
             marginBottom: '20px', 
             width: '100%', 
             padding: '12px', 
             fontSize: '0.8rem', 
             fontWeight: '800',
             borderRadius: '12px', 
             background: 'var(--accent-ochre)', 
             border: 'none', 
             color: 'var(--overlay-heavy-bg)',
             cursor: 'pointer',
             display: 'flex',
             alignItems: 'center',
             justifyContent: 'center',
             gap: '8px',
             boxShadow: '0 4px 15px var(--accent-glow)',
             overflow: 'hidden'
          }}
        >
          <Plus size={18} /> {showSidebar && "NEW SESSION"}
        </button>

        <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {[
            { id: 'chat', icon: MessageSquare, label: 'Observer' },
            { id: 'graph', icon: Activity, label: 'Logical Graph' },
            { id: 'swarm', icon: Network, label: 'Systems Dashboard' },
            { id: 'registry', icon: Puzzle, label: 'Tool Registry' },
            { id: 'settings', icon: Settings, label: 'Cognition Settings' }
          ].map(item => (
            <div 
              key={item.id}
              className={`nav-item ${activeView === item.id ? 'active' : ''}`} 
              onClick={() => setActiveView(item.id)}
              style={{ 
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', borderRadius: '10px', 
                background: activeView === item.id ? 'var(--nav-hover-bg)' : 'transparent',
                border: activeView === item.id ? '1px solid var(--accent-ochre)' : '1px solid transparent',
                opacity: activeView === item.id ? 1 : 0.6,
                justifyContent: showSidebar ? 'flex-start' : 'center'
              }}
              title={!showSidebar ? item.label : ''}
            >
              <item.icon size={20} color={activeView === item.id ? 'var(--accent-ochre)' : 'inherit'} /> 
              {showSidebar && <span style={{ fontWeight: activeView === item.id ? '700' : '500', fontSize: '0.9rem' }}>{item.label}</span>}
            </div>
          ))}
        </nav>
        
        {/* Sessions Flyout Button */}
        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '10px' }}>
          <button 
            onClick={() => setShowSessionsPane(!showSessionsPane)} 
            style={{ 
              width: '100%', 
              padding: '12px', 
              fontSize: '0.8rem', 
              fontWeight: '800',
              borderRadius: '12px', 
              background: showSessionsPane ? 'var(--accent-ochre)' : 'var(--nav-hover-bg)', 
              border: showSessionsPane ? 'none' : '1px solid var(--accent-ochre)',
              color: showSessionsPane ? 'var(--overlay-heavy-bg)' : 'var(--text-primary)', 
              cursor: 'pointer',
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              gap: '8px', 
              boxShadow: showSessionsPane ? '0 4px 15px var(--accent-glow)' : 'none',
              transition: 'all 0.2s',
              overflow: 'hidden'
            }}
          >
            <History size={18} /> {showSidebar && "SESSIONS"}
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button onClick={triggerKillSwitch} className="btn-error" style={{ 
            width: '100%', 
            padding: '12px', 
            fontSize: '0.8rem', 
            fontWeight: '800',
            borderRadius: '12px', 
            background: 'var(--accent-red)', 
            border: 'none', 
            color: '#fff', 
            cursor: 'pointer',
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            gap: '8px', 
            boxShadow: '0 4px 15px rgba(255, 68, 68, 0.4)',
            transition: 'all 0.2s',
            overflow: 'hidden'
          }}>
            <Power size={18} /> {showSidebar && "KILL SWITCH"}
          </button>
        </div>
      </div>

      {/* Flyout Sessions Pane */}
      <AnimatePresence>
        {showSessionsPane && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'fixed',
                top: 0, left: 0, right: 0, bottom: 0,
                background: 'rgba(0,0,0,0.5)',
                zIndex: 40
              }}
              onClick={() => setShowSessionsPane(false)}
            />
            <motion.div
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -20, opacity: 0 }}
              style={{
                position: 'fixed',
                top: '20px',
                bottom: '20px',
                left: showSidebar ? '290px' : '90px',
                width: '320px',
                background: 'var(--panel-bg)',
                border: '1px solid var(--border-color)',
                borderRadius: '16px',
                boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
                zIndex: 45,
                display: 'flex',
                flexDirection: 'column',
                padding: '20px',
                transition: 'left 0.3s ease'
              }}
            >
               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <h3 style={{ fontSize: '1rem', margin: 0, color: 'var(--accent-ochre)', fontWeight: '900', letterSpacing: '1px' }}>SESSIONS</h3>
               </div>

               <div style={{ position: 'relative', marginBottom: '20px' }}>
                 <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', opacity: 0.4 }} />
                 <input 
                   placeholder="Search..."
                   value={sessionSearch}
                   onChange={(e) => setSessionSearch(e.target.value)}
                   style={{ 
                     width: '100%', 
                     padding: '10px 10px 10px 32px', 
                     fontSize: '0.85rem', 
                     borderRadius: '8px', 
                     border: '1px solid var(--border-color)', 
                     background: 'var(--bg-color)', 
                     color: 'var(--text-primary)' 
                   }}
                 />
               </div>
               
               <div className="scroll-container" style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, overflowY: 'auto', paddingRight: '5px' }}>
                  {(sessions || [])
                    .filter(s => {
                      if (!s) return false;
                      const title = s.title || '';
                      const id = s.id || '';
                      const search = sessionSearch || '';
                      return title.toLowerCase().includes(search.toLowerCase()) || id.toLowerCase().includes(search.toLowerCase());
                    })
                    .map(session => (
                    <div 
                      key={session.id || Math.random()} 
                      onClick={() => {
                        loadSession(session.id);
                        setShowSessionsPane(false);
                      }}
                      style={{ 
                        fontSize: '0.8rem', 
                        padding: '12px 16px', 
                        borderRadius: '10px', 
                        cursor: 'pointer',
                        background: currentSessionId === session.id ? 'var(--accent-ochre)' : 'var(--nav-hover-bg)',
                        color: currentSessionId === session.id ? 'var(--overlay-heavy-bg)' : 'var(--text-primary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        border: currentSessionId === session.id ? '1px solid transparent' : '1px solid var(--border-color)',
                        fontWeight: currentSessionId === session.id ? '800' : '500',
                        transition: 'all 0.2s'
                      }}
                      title={session.title || 'Session'}
                    >
                      <Clock size={12} style={{ marginRight: '8px', verticalAlign: 'middle', opacity: 0.7 }} />
                      {session.title || session.id || 'Unknown Session'}
                    </div>
                  ))}
               </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <div className="main-content">
        <header className="glass-panel" style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: '30px', 
          alignItems: 'center',
          padding: '20px',
          borderRadius: '24px'
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <h1 style={{ fontSize: '1.2rem', fontWeight: '900', letterSpacing: '0.5px', margin: 0 }}>
              SESSION: <span style={{ color: 'var(--accent-ochre)' }}>
                {(() => {
                  if (!currentSessionId) return 'INITIALIZING';
                  const activeSession = (sessions || []).find(s => s.id === currentSessionId);
                  return activeSession && activeSession.title ? activeSession.title.toUpperCase() : currentSessionId.split('-')[0].toUpperCase();
                })()}
              </span>
            </h1>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
             {/* Unified Action Row */}
             <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px', background: 'rgba(0,0,0,0.1)', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
                <button 
                  onClick={() => setShowCanvas(!showCanvas)} 
                  className={`action-button ${showCanvas ? 'active' : ''}`}
                  title={showCanvas ? 'Close Research Canvas' : 'Open Research Canvas'}
                >
                  <Layout size={16} /> 
                  <span style={{ fontSize: '0.7rem' }}>CANVAS</span>
                </button>

                <button 
                  onClick={toggleTheme} 
                  className="action-button"
                  title="Toggle Theme"
                >
                  {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                </button>

                <button 
                  onClick={() => handleOpenHelp('basics')}
                  className="action-button"
                  style={{ border: '1px solid var(--accent-cyan)', color: 'var(--accent-cyan)' }}
                  title="Active Help"
                >
                  <HelpCircle size={16} />
                </button>
             </div>

             {/* Traffic Light Status Indicator */}
             <div className={`status-pill status-${agentStatus}`} style={{ 
               padding: '8px 16px', 
               borderRadius: '12px', 
               background: 'var(--panel-bg)', 
               border: '1px solid var(--border-color)', 
               display: 'flex', 
               alignItems: 'center', 
               gap: '10px',
               boxShadow: '0 4px 15px rgba(0,0,0,0.1)'
             }}>
                <span className="status-dot"></span>
                <span style={{ fontSize: '0.75rem', fontWeight: '900', color: 'var(--text-primary)', letterSpacing: '1px' }}>
                  {agentStatus.toUpperCase()}
                </span>
             </div>
          </div>
        </header>

        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          {activeView === 'chat' && (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px 15px 0' }}>
                <h3 style={{ fontSize: '0.9rem', fontWeight: '800', letterSpacing: '1px', opacity: 0.6 }}>OBSERVER TERMINAL</h3>
                <button 
                  onClick={() => setShowDashboardOverlay(!showDashboardOverlay)}
                  className="button-secondary"
                  style={{ fontSize: '0.7rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  <Activity size={14} />
                  {showDashboardOverlay ? 'HIDE SYSTEM STATS' : 'SHOW SYSTEM STATS'}
                </button>
              </div>
              
              {showDashboardOverlay && (
                <div style={{ padding: '0 20px 20px 0', height: '300px' }}>
                  <SystemsDashboard compact />
                </div>
              )}

              {/* Canvas/Chat Split Row */}
              {(() => {
                const CANVAS_SPLITS = [
                  { label: 'Collapsed', chat: 'calc(100% - 60px)', canvas: '60px' },
                  { label: '75 / 25', chat: '75%', canvas: '25%' },
                  { label: '50 / 50', chat: '50%', canvas: '50%' },
                  { label: '40 / 60', chat: '40%', canvas: '60%' },
                  { label: '100%', chat: '0%', canvas: '100%' },
                ];
                // default to 75/25 if index is out of bounds (it shouldn't be)
                const activeSplit = CANVAS_SPLITS[canvasSplitIndex] || CANVAS_SPLITS[1];
                const chatWidth = showCanvas ? activeSplit.chat : '100%';
                const canvasWidth = activeSplit.canvas;
                const isFullCanvas = chatWidth === '0%';

                return (
                  <div style={{ display: 'flex', flexDirection: 'row', flex: 1, minHeight: 0, gap: showCanvas ? '20px' : '0', paddingRight: showCanvas ? '10px' : '0' }}>
                    {/* Chat Panel */}
                    {chatWidth !== '0%' && (
                      <div className="chat-grid" style={{ 
                        display: 'grid', 
                        gridTemplateColumns: '1fr', 
                        gap: '24px', 
                        height: '100%', 
                        overflow: 'hidden',
                        minWidth: 0,
                        width: chatWidth,
                        transition: 'width 0.3s ease'
                      }}>
                        <div className="card" style={{ 
                          display: 'flex', 
                          flexDirection: 'column', 
                          height: '100%', 
                          overflow: 'hidden', 
                          padding: '20px',
                          minWidth: 0
                        }}>
                          <div className="messages-container" style={{ width: '100%', minWidth: 0 }}>
                            <AnimatePresence>
                              {messages.map(msg => (
                                <motion.div 
                                  initial={{ opacity: 0, y: 10 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  key={msg.id}
                                  style={{ 
                                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                    maxWidth: '96%',
                                    background: msg.role === 'user' ? 'var(--user-bubble-bg)' : msg.content.includes('[SYSTEM ERROR]') ? 'rgba(226, 149, 120, 0.05)' : 'rgba(255, 255, 255, 0.03)',
                                    color: msg.role === 'user' ? 'var(--user-bubble-text)' : 'var(--text-primary)',
                                    padding: msg.role === 'user' ? '14px 18px' : '14px 40px 14px 20px',
                                    borderRadius: '18px',
                                    marginLeft: msg.role === 'user' ? 'auto' : '0',
                                    border: msg.role === 'user' ? '1px solid rgba(255,255,255,0.1)' : msg.content.includes('[SYSTEM ERROR]') ? '1px solid var(--accent-red)' : '1px solid var(--glass-border)',
                                    position: 'relative',
                                    overflowWrap: 'anywhere',
                                    wordBreak: 'normal',
                                    boxShadow: 'var(--card-shadow)'
                                  }}
                                >
                                  <div className="markdown-body">
                                    {msg.content && msg.content.includes('[SYSTEM ERROR]') ? (
                                      <div style={{ padding: '10px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-red)', fontWeight: '900', marginBottom: '10px', fontSize: '0.85rem', letterSpacing: '1px' }}>
                                          <Activity size={16} /> RECOVERY LOOP ENGAGED
                                        </div>
                                        <pre style={{ margin: 0, fontSize: '0.75rem', opacity: 0.85, color: 'var(--text-primary)', whiteSpace: 'pre-wrap', fontFamily: 'monospace', background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px', borderLeft: '4px solid var(--accent-red)' }}>
                                          {msg.content.replace('[SYSTEM ERROR]', '').trim()}
                                        </pre>
                                      </div>
                                    ) : (
                                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.content}
                                      </ReactMarkdown>
                                    )}
                                  </div>
                                  {msg.role === 'assistant' && (
                                    <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                                      <div 
                                        className="tear-away-button" 
                                        title="Push to Canvas"
                                        onClick={() => handlePushToCanvas('MD', msg.content)}
                                        style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '4px 8px', borderRadius: '6px', cursor: 'pointer', background: 'var(--nav-hover-bg)' }}
                                      >
                                        <Layout size={12} color="var(--accent-cyan)" />
                                        <span style={{ fontSize: '0.6rem', color: 'var(--accent-cyan)', fontWeight: 'bold' }}>PUSH TO CANVAS</span>
                                      </div>
                                    </div>
                                  )}
                                </motion.div>
                              ))}
                              <div ref={messagesEndRef} />
                            </AnimatePresence>
                          </div>
                          
                           <div className="input-container">
                               <textarea 
                                 ref={textareaRef}
                                 className="chat-input"
                                 value={input}
                                 onChange={(e) => setInput(e.target.value)}
                                 onKeyDown={(e) => {
                                   if (e.key === 'Enter' && !e.shiftKey) {
                                     e.preventDefault();
                                     handleRun();
                                   }
                                 }}
                                 disabled={isHalted}
                                 placeholder={isHalted ? "SYSTEM HALTED" : "Assign task or ask a question..."} 
                                 rows={1}
                               />
                               <button 
                                 onClick={handleRun} 
                                 className="btn-primary" 
                                 style={{ padding: '14px', height: 'fit-content' }}
                               >
                                 <Send size={20} />
                               </button>
                           </div>
                        </div>

                        {/* Orchestration Sidebar removed for de-cluttering Phase 33 */}
                      </div>
                    )}

                    {/* Canvas Panel */}
                    {showCanvas && (
                      <div className="canvas-sidebar" style={{ width: canvasWidth, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative', transition: 'width 0.3s ease' }}>
                         <div style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 100, display: 'flex', alignItems: 'center', background: 'var(--header-bg)', padding: '4px 8px', borderRadius: '12px', border: '1px solid var(--border-color)', backdropFilter: 'blur(10px)', visibility: canvasSplitIndex === 0 ? 'hidden' : 'visible' }}>
                           <select 
                             value={canvasSplitIndex}
                             onChange={(e) => setCanvasSplitIndex(Number(e.target.value))}
                             style={{
                               background: 'transparent',
                               border: 'none',
                               color: 'var(--text-primary)',
                               fontSize: '0.75rem',
                               fontWeight: '900',
                               outline: 'none',
                               cursor: 'pointer'
                             }}
                             title="Select Canvas Split Ratio"
                           >
                             <option value={0} style={{ background: 'var(--bg-color)' }}>Collapsed</option>
                             <option value={1} style={{ background: 'var(--bg-color)' }}>75/25 (Chat/Canvas)</option>
                             <option value={2} style={{ background: 'var(--bg-color)' }}>50/50 Split</option>
                             <option value={3} style={{ background: 'var(--bg-color)' }}>40/60 (Chat/Canvas)</option>
                             <option value={4} style={{ background: 'var(--bg-color)' }}>100% (Canvas Only)</option>
                           </select>
                         </div>
                        <CanvasPanel 
                          showFull={chatWidth === '0%'} 
                          isCollapsed={canvasSplitIndex === 0}
                          onRestore={() => setCanvasSplitIndex(1)}
                          onToggleFull={() => setCanvasSplitIndex(canvasSplitIndex === 4 ? 2 : 4)} 
                        />
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}

          { activeView === 'graph' && <div className="flex-column-scroll" style={{ flex: 1, height: '100%' }}><GraphView onInfo={() => handleOpenHelp('graph')} /></div>}
          { activeView === 'swarm' && <div className="scroll-container" style={{ flex: 1 }}><SystemsDashboard /></div>}
          { activeView === 'registry' && <div className="scroll-container" style={{ flex: 1 }}><ToolRegistry /></div>}
          { activeView === 'forge' && <div className="scroll-container" style={{ flex: 1 }}><SkillForge /></div>}
          { activeView === 'settings' && <div className="scroll-container" style={{ flex: 1 }}><SettingsView onOpenHelp={handleOpenHelp} onTriggerVision={triggerVision} onManualCam={() => setShowPrivacyModal('webcam')} /></div>}
          { activeView === 'help' && <div className="scroll-container" style={{ flex: 1 }}><HelpView topic={helpTopic} onClearTopic={() => setHelpTopic(null)} /></div>}
        </div>
      </div>

      {isHalted && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.9)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 5000 }}>
          <div style={{ padding: '60px', borderRadius: '24px', background: '#000', border: '8px solid var(--accent-red)', textAlign: 'center', boxShadow: '0 0 100px rgba(255, 0, 0, 0.5)' }}>
            <Power size={80} color="var(--accent-red)" style={{ marginBottom: '30px' }} />
            <h1 style={{ color: 'var(--accent-red)', fontSize: '4rem', fontWeight: '900', marginBottom: '20px' }}>SYSTEM HALTED</h1>
            <p style={{ fontSize: '1.5rem', opacity: 0.8 }}>Emergency Cut-Off Active. Reboot required.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
