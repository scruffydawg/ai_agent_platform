import React, { useState, useEffect } from 'react';
import { 
  Library, 
  Search, 
  Upload, 
  FileText, 
  Book, 
  Code, 
  Terminal, 
  Plus, 
  X,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const KnowledgeHub = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // 'idle', 'uploading', 'success', 'error'
  const [selectedCategory, setSelectedCategory] = useState('All');

  const categories = [
    { name: 'All', icon: Library, count: 0 },
    { name: 'Coding', icon: Code, count: 0 },
    { name: 'N8N', icon: Terminal, count: 0 },
    { name: 'Architecture', icon: Book, count: 0 },
    { name: 'Project Docs', icon: FileText, count: 0 },
  ];

  const handleSearch = async (e) => {
    const q = e.target.value;
    setSearchQuery(q);
    if (q.length > 2) {
      setIsSearching(true);
      try {
        const res = await axios.get(`http://localhost:8001/knowledge/search?q=${q}`);
        setSearchResults(res.data.results || []);
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setIsSearching(false);
      }
    } else {
      setSearchResults([]);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', selectedCategory === 'All' ? 'general' : selectedCategory.toLowerCase());

    try {
      await axios.post('http://localhost:8001/knowledge/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadStatus('success');
      setTimeout(() => setUploadStatus(null), 3000);
    } catch (err) {
      console.error("Upload failed:", err);
      setUploadStatus('error');
      setTimeout(() => setUploadStatus(null), 5000);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 h-full overflow-y-auto custom-scrollbar">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Knowledge Hub
          </h1>
          <p className="text-slate-400 mt-2">Manage and search technical reference documentation for your swarm.</p>
        </div>
        
        <div className="relative group">
          <input
            type="text"
            placeholder="Search the library... (Cmd+K)"
            value={searchQuery}
            onChange={handleSearch}
            className="w-full md:w-96 pl-12 pr-4 py-3 bg-slate-900/50 border border-slate-700/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all text-slate-200"
          />
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-400 transition-colors" size={20} />
          {isSearching && <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 text-emerald-500 animate-spin" size={18} />}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Categories Sidebar */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 px-2">Spaces</h2>
          <div className="space-y-1">
            {categories.map((cat) => (
              <button
                key={cat.name}
                onClick={() => setSelectedCategory(cat.name)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
                  selectedCategory === cat.name 
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                  : 'text-slate-400 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <cat.icon size={18} />
                  <span className="font-medium">{cat.name}</span>
                </div>
                <span className="text-xs bg-slate-800 px-2 py-0.5 rounded-full">{cat.count}</span>
              </button>
            ))}
          </div>

          {/* Upload Card */}
          <div className="mt-8 p-6 bg-slate-900/30 border border-dashed border-slate-700 rounded-2xl flex flex-col items-center text-center space-y-4">
            <div className="w-12 h-12 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-400">
              <Upload size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">Ingest New Doc</p>
              <p className="text-xs text-slate-500 mt-1">PDF, MD, or Text</p>
            </div>
            <label className="cursor-pointer bg-emerald-500 hover:bg-emerald-600 text-slate-900 px-4 py-2 rounded-lg text-sm font-bold transition-all w-full">
              Choose File
              <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf,.md,.txt" />
            </label>
            
            <AnimatePresence>
              {uploadStatus && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={`flex items-center gap-2 text-xs font-medium ${
                    uploadStatus === 'success' ? 'text-emerald-400' : 
                    uploadStatus === 'error' ? 'text-rose-400' : 'text-cyan-400'
                  }`}
                >
                  {uploadStatus === 'uploading' && <Loader2 size={14} className="animate-spin" />}
                  {uploadStatus === 'success' && <CheckCircle2 size={14} />}
                  {uploadStatus === 'error' && <AlertCircle size={14} />}
                  <span>
                    {uploadStatus === 'uploading' ? 'Analyzing...' : 
                     uploadStatus === 'success' ? 'Ingested Successfully' : 'Upload Failed'}
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-3 space-y-6">
          {searchResults.length > 0 ? (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Search Results</h2>
              <div className="grid grid-cols-1 gap-4">
                {searchResults.map((result, i) => (
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    key={i}
                    className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-emerald-500/30 transition-all group cursor-pointer"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-800 rounded-lg group-hover:bg-emerald-500/10 group-hover:text-emerald-400 transition-colors">
                          <FileText size={18} />
                        </div>
                        <div>
                          <p className="text-slate-200 font-medium">{result.metadata.filename}</p>
                          <p className="text-xs text-slate-500">Match found in chunk #{result.metadata.chunk_index}</p>
                        </div>
                      </div>
                      <span className="text-[10px] uppercase font-bold tracking-widest text-slate-600 bg-slate-800/50 px-2 py-1 rounded">
                        {result.metadata.category || 'Reference'}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-slate-400 line-clamp-2 italic">
                      "...{result.content.substring(0, 200)}..."
                    </p>
                  </motion.div>
                ))}
              </div>
            </div>
          ) : searchQuery ? (
            <div className="flex flex-col items-center justify-center p-20 text-slate-500 space-y-4 border border-dashed border-slate-800 rounded-3xl">
              <Search size={48} className="text-slate-700" />
              <div className="text-center">
                <p className="text-lg font-medium">No matches found</p>
                <p className="text-sm">Try generic terms or check category filters.</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Bento-style Feature Cards */}
              <div className="p-8 rounded-3xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/5 border border-emerald-500/20 col-span-1 md:col-span-2 relative overflow-hidden group">
                <div className="relative z-10 space-y-4">
                  <div className="w-14 h-14 bg-emerald-500 text-slate-900 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                    <Library size={30} />
                  </div>
                  <h3 className="text-2xl font-bold text-slate-100">Intelligent Reference Library</h3>
                  <p className="text-slate-400 max-w-lg">
                    This library is shared globally across your swarm. When an agent needs a technical specification or a coding rule, they'll check here first.
                  </p>
                  <div className="flex gap-4">
                    <div className="px-3 py-1 bg-emerald-500/10 rounded-full border border-emerald-500/20 text-xs text-emerald-400 font-bold">RAG Enabled</div>
                    <div className="px-3 py-1 bg-cyan-500/10 rounded-full border border-cyan-500/20 text-xs text-cyan-400 font-bold">Vector Search</div>
                  </div>
                </div>
                <Library className="absolute -right-10 -bottom-10 text-emerald-500/5 w-64 h-64 group-hover:scale-110 transition-transform duration-700" />
              </div>

              <div className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800">
                 <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                   <Code size={20} className="text-emerald-400" />
                   Coding Standards
                 </h3>
                 <p className="text-sm text-slate-400 mt-2">Latest React, Tailwind, and FastAPI best practices.</p>
                 <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                   <CheckCircle2 size={14} className="text-emerald-500" />
                   Upvoted by Architect
                 </div>
              </div>

              <div className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800 shadow-xl shadow-black/20">
                 <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                   <Terminal size={20} className="text-cyan-400" />
                   N8N Workflows
                 </h3>
                 <p className="text-sm text-slate-400 mt-2">Documentation for custom nodes and API integrations.</p>
                 <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                   <CheckCircle2 size={14} className="text-emerald-500" />
                   Verified by Guide
                 </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeHub;
