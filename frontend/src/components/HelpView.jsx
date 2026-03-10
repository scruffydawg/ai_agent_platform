import React from 'react';
import { Zap, Shield, Network, Hammer, Search, HelpCircle } from 'lucide-react';

const HelpView = ({ topic, onClearTopic }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', margin: '0 auto', padding: '20px' }}>
      <header style={{ textAlign: 'center', marginBottom: '20px' }}>
        <img src="/ehecatl.png" style={{ width: '120px', height: '120px', borderRadius: '50%', border: '3px solid var(--accent-ochre)', marginBottom: '16px', boxShadow: '0 0 25px rgba(212, 163, 115, 0.5)' }} alt="Guide" />
        <h1 style={{ fontSize: '2rem', fontWeight: '900', color: 'var(--accent-ochre)' }}>🌬️ GUIDE HELP</h1>
        <p style={{ opacity: 0.7 }}>The Flute Path — Clarity, Focus, and Agentic Logic</p>
        {topic && (
           <button onClick={onClearTopic} style={{ marginTop: '10px', background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px 12px', borderRadius: '4px' }}>
              ← Show All Topics
           </button>
        )}
      </header>

      <div className="card" style={{ border: topic === 'basics' ? '2px solid var(--accent-ochre)' : '1px solid var(--border-color)', background: topic === 'basics' ? 'var(--accent-translucent)' : 'var(--panel-bg)' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-ochre)', marginBottom: '12px' }}>
          <Zap size={20} /> TL;DR — THE GUIDE APPROACH
        </h3>
        <p>Guide is your <strong>private, local-first AI swarm</strong>. All models run on your hardware (Tai Mae via Tailscale). Nothing leaves your network. Your data is stored in <code>/home/scruffydawg/guide_storage</code>.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="card" style={{ border: topic === 'safety' ? '2px solid var(--accent-ochre)' : '1px solid var(--border-color)' }}>
          <h4 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}><Shield size={18} color="var(--accent-red)" /> SAFETY & CONTROL</h4>
          <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li><strong>Kill Switch:</strong> Red button — instantly halts all agents.</li>
            <li><strong>Trigger Only:</strong> Nothing runs until you say so.</li>
            <li><strong>Privacy Gate:</strong> Vision tasks always request authorization first.</li>
            <li><strong>Sandbox:</strong> Forged skills land in <code>sandbox/</code> before promotion.</li>
          </ul>
        </div>

        <div className="card" style={{ border: (topic === 'graph' || topic === 'canvas') ? '2px solid var(--accent-ochre)' : '1px solid var(--border-color)' }}>
          <h4 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}><Network size={18} color="var(--accent-cyan)" /> GUIDE VIEWS</h4>
          <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li><strong>Observer:</strong> Chat with the swarm directly.</li>

            <li><strong>Research Canvas:</strong> Infinite tldraw whiteboard for ideas.</li>
            <li><strong>Swarm Mind:</strong> Real-time Tailnet node telemetry.</li>
          </ul>
        </div>
      </div>

      <section className="card">
        <h2 style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>🧠 THE SWARM MIND (AGENT SOULS)</h2>
        <p>Your Guide is powered by a swarm of specialized agents, each with a human-readable <strong>.md Soul</strong> that defines their behavior:</p>
        <ul style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
          <li><strong>Observer:</strong> The bridge. Listen, clarifies, and coordinates the swarm.</li>
          <li><strong>Researcher:</strong> The harvester. Specialist in SearXNG and multi-tier source ranking.</li>
          <li><strong>Analyst:</strong> The logic engine. Synthesizes research into actionable insights.</li>
          <li><strong>Architect:</strong> The lead dev. Ensures logic consistency and "No Dead Loop" safety.</li>
        </ul>
        <p style={{ marginTop: '12px', fontSize: '0.85rem', opacity: 0.7 }}><em>Find these in `src/agents/experts/` to see exactly how they think.</em></p>
      </section>

      <section className="card">
        <h2 style={{ color: 'var(--accent-ochre)', marginBottom: '12px' }}>🌊 SYSTEM COGNITION & FLOW</h2>
        <p>Guide is self-aware. We have vectorized the entire architecture into <strong>Qdrant</strong>.</p>
        <div style={{ background: 'var(--header-bg)', padding: '15px', borderRadius: '8px', borderLeft: '4px solid var(--accent-ochre)' }}>
          <strong>The Strong Flow:</strong> If a task feels complex, use the <strong>[TEAR AWAY]</strong> button on any message to pin it to your <strong>Creative Canvas</strong>. This keeps your focus locked while the swarm works.
        </div>
        <p style={{ marginTop: '12px' }}>Try asking: <em>"How are your expert souls configured?"</em> or <em>"Explain the Flute Path logic."</em></p>
      </section>

      <section className="card">
        <h2 style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>🛠️ BASE INFRASTRUCTURE</h2>
        <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
          <li><strong>Model:</strong> Qwen 2.5 32B (Local-First Priority)</li>
          <li><strong>VDB:</strong> Qdrant (Tailscale Mesh)</li>
          <li><strong>Search:</strong> SearXNG (Geo-Bias: us-CO)</li>
          <li><strong>Storage:</strong> <code>/home/scruffydawg/guide_storage</code></li>
        </ul>
      </section>

      <div className="card" style={{ border: '1px solid var(--border-color)' }}>
        <h4 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}><Hammer size={18} color="var(--accent-ochre)" /> GUIDE'S FORGE</h4>
        <p>Manifest new Skills, MCPs, or Hybrids through guided AI conversation. Guide (Ehecatl) leads the interview, researches APIs, and drafts architecture — you approve before anything is written.</p>
        <p style={{ marginTop: '8px', opacity: 0.6, fontSize: '0.85rem' }}>Fully integrated with Google Workspace, Office 365, Docker, n8n, and more.</p>
      </div>

      <div className="card" style={{ border: topic === 'settings' ? '2px solid var(--accent-ochre)' : '1px solid var(--border-color)' }}>
        <h4 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}><Search size={18} color="var(--accent-green)" /> STORAGE & SEARCH</h4>
        <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <li><strong>Storage Root:</strong> <code>/home/scruffydawg/guide_storage</code></li>
          <li><strong>Vector Memory:</strong> Qdrant at <code>localhost:6333</code></li>
          <li><strong>SQL Memory:</strong> PostgreSQL at <code>localhost:5432</code></li>
          <li><strong>Search:</strong> SearXNG (geo-prioritized to Colorado) at <code>localhost:8080</code></li>
        </ul>
      </div>

      <footer style={{ textAlign: 'center', padding: '20px', opacity: 0.4, fontSize: '0.8rem' }}>
        Guide — Earth & Ether Design System · ADHD Clarity Optimized · Tailscale-First Mesh
      </footer>
    </div>
  );
};

export default HelpView;
