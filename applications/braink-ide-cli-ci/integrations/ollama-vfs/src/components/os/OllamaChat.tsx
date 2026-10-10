import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Sparkles, RotateCcw, AlertCircle, X } from 'lucide-react';

export const OllamaChat: React.FC = () => {
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [lastMetadata, setLastMetadata] = useState<any>(null);

  useEffect(() => {
    async function fetchModels() {
      try {
        const res = await fetch('/api/ollama/tags');
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Ollama unavailable');
        if (data.models) {
          const names = data.models.map((m: any) => m.name);
          setModels(names);
          if (names.length > 0 && !names.includes(selectedModel)) {
            setSelectedModel(names[0]);
          }
        }
      } catch (e) { setSystemError('Ollama model discovery failed; no models have been verified.'); }
    }
    fetchModels();
  }, []);

  const [systemError, setSystemError] = useState<string | null>(null);

  const handleClearContext = () => {
    setMessages([]);
    setSystemError(null);
    setLastMetadata(null);
  };

  const handleSend = async () => {
    if (!input.trim() || isTyping || !selectedModel) return;

    const userMsg = input.trim();
    setInput('');
    setSystemError(null);
    const newMessages = [...messages, { role: 'user' as const, content: userMsg }];
    setMessages(newMessages);
    setIsTyping(true);

    const contextPayload = newMessages;

    try {
      const res = await fetch('/api/ollama/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: selectedModel,
          messages: contextPayload,
          stream: false
        })
      });

      const data = await res.json();
      
      if (!res.ok || data.error) {
        setSystemError(`${data.error}: ${data.detail || 'Substrate communication failure'}`);
      } else if (data.message) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.message.content }]);
        if (data.braink_metadata) {
          setLastMetadata(data.braink_metadata);
        }
      }
    } catch (err) {
      setSystemError('Failed to communicate with inference substrate. Ensure server is active.');
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 font-sans">
      {/* Header */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between bg-slate-900/50">
         <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
               <Sparkles className="w-4 h-4 text-blue-400" />
            </div>
            <div>
               <div className="flex items-center gap-2">
                 <h3 className="text-[11px] font-bold text-white uppercase tracking-widest">Ollama Substrate</h3>
                 <span className="text-[8px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                   Context: {messages.filter(m => m.role === 'user').length} turns
                 </span>
               </div>
               <div className="flex items-center gap-2 mt-0.5">
                  <select 
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="bg-slate-800 border border-white/10 text-[9px] text-slate-300 rounded px-1 py-0.5 focus:outline-none"
                  >
                    {models.length > 0 ? models.map(m => <option key={m} value={m}>{m}</option>) : <option value="">No verified models</option>}
                  </select>
                  <button
                    onClick={handleClearContext}
                    title="Refresh context window and clear memory buffer"
                    className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-white/10 transition-colors"
                  >
                    <RotateCcw className="w-2.5 h-2.5 text-slate-400" />
                    <span>Reset Context</span>
                  </button>
               </div>
            </div>
         </div>
         <div className="flex flex-col items-end gap-1">
           <div className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
              <span className="text-[8px] font-bold text-emerald-400">{models.length ? 'MODEL INVENTORY OBSERVED' : 'SERVICE UNVERIFIED'}</span>
           </div>
           {lastMetadata && (
             <div className="flex flex-col items-end">
               <div className="text-[7px] text-slate-500 font-mono">
                 COORD: Λ-{lastMetadata.manifold_coordinate.toString(16).toUpperCase()}
               </div>
               <div className="text-[7px] text-blue-400 font-mono font-bold">
                 ADDR: {lastMetadata.injective_address}
               </div>
             </div>
           )}
         </div>
      </div>

      {/* Transient System Error Banner (Isolated from context tokens) */}
      {systemError && (
        <div className="mx-4 mt-3 p-3 rounded-lg bg-red-950/40 border border-red-500/30 flex items-start justify-between gap-3 text-red-200">
          <div className="flex items-center gap-2 text-[11px]">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{systemError}</span>
          </div>
          <button 
            onClick={() => setSystemError(null)}
            className="text-red-400 hover:text-red-200 p-0.5 rounded transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex gap-4 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center border ${
                msg.role === 'user' ? 'bg-slate-800 border-slate-700' : 'bg-blue-600 border-blue-500'
              }`}>
                {msg.role === 'user' ? <User className="w-4 h-4 text-slate-300" /> : <Bot className="w-4 h-4 text-white" />}
              </div>
              <div className={`p-4 rounded-2xl text-[12px] leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user' 
                ? 'bg-slate-900 text-slate-200 border border-white/5 rounded-tr-none' 
                : 'bg-blue-600/10 text-blue-100 border border-blue-500/20 rounded-tl-none'
              }`}>
                {msg.content}
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="flex gap-4 items-center px-4">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center animate-pulse">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-bounce [animation-delay:-0.3s]" />
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-bounce [animation-delay:-0.15s]" />
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-bounce" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/5 bg-slate-900/30">
        <div className="relative group">
          <input 
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={models.length === 0 ? "Ollama seems offline..." : "Enter inference query..."}
            className="w-full bg-slate-950 border border-white/10 rounded-xl py-3 px-4 pr-12 text-[12px] text-white focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-slate-600"
          />
          <button 
            onClick={handleSend}
            disabled={isTyping}
            className="absolute right-2 top-1.5 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="mt-2 text-center">
          <span className="text-[8px] text-slate-600 font-mono uppercase tracking-[0.2em]">Actual Ollama inference // deterministic proxy layer</span>
        </div>
      </div>
    </div>
  );
};
