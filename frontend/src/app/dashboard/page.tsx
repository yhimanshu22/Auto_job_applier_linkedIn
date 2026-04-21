"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { signOut } from "next-auth/react";

const CONFIG_FILES = ["personals.py", "search.py", "settings.py", "questions.py"];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState(CONFIG_FILES[0]);
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    fetchConfig(activeTab);
  }, [activeTab]);

  const fetchConfig = async (filename: string) => {
    setIsLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`http://localhost:8000/api/config/${filename}`);
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();
      setContent(data.content || "");
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Error loading configuration. Ensure backend is running.' });
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfig = async () => {
    setIsSaving(true);
    setMessage(null);
    try {
      const res = await fetch(`http://localhost:8000/api/config/${activeTab}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error("Failed to save");
      setMessage({ type: 'success', text: 'Configuration saved successfully!' });
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Error saving configuration.' });
    } finally {
      setIsSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const startBot = async () => {
    setMessage(null);
    try {
      const res = await fetch(`http://localhost:8000/api/bot/start`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to start bot");
      setMessage({ type: 'success', text: 'Bot successfully started!' });
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Error starting bot.' });
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200 font-sans selection:bg-accent/30">
      {/* Top Navbar */}
      <nav className="border-b border-zinc-800/50 bg-zinc-950/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center group cursor-default">
              <div className="size-8 rounded-lg bg-gradient-to-br from-accent to-purple-800 flex items-center justify-center text-white font-serif font-bold text-xl shadow-lg shadow-accent/20">
                A
              </div>
              <span className="ml-3 font-serif text-xl font-semibold tracking-tight text-white transition-colors">
                LinkdApply Dashboard
              </span>
            </div>
            <div className="flex items-center space-x-6">
               <div className="flex items-center gap-3 px-4 py-1.5 rounded-full bg-zinc-900 border border-zinc-800">
                  <div className="size-2 rounded-full bg-emerald-500 animate-pulse"></div>
                  <span className="text-xs font-medium text-zinc-400">System Online</span>
               </div>
            </div>
          </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        {/* Header Section */}
        <header className="mb-12 flex flex-col md:flex-row md:items-end md:justify-between gap-6">
          <div className="space-y-2">
            <h1 className="font-serif text-4xl font-medium tracking-tight text-white">
              Configuration Dashboard
            </h1>
            <p className="text-zinc-500 text-sm max-w-lg">Manage your application parameters, adjust search settings, and verify bot credentials in real-time.</p>
          </div>
          <div className="shrink-0">
            <button
              onClick={startBot}
              className="purple-gradient-button inline-flex items-center px-8 py-3.5 rounded-xl text-white font-semibold shadow-2xl hover:scale-[1.02] transition-all"
            >
              <svg className="size-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Start Bot Sequence
            </button>
          </div>
        </header>

        {/* Status Message */}
        {message && (
          <div className={`mb-8 p-4 rounded-xl flex items-center gap-3 transition-all animate-in fade-in slide-in-from-top-2 ${
            message.type === 'success' 
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' 
              : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
          }`}>
            <div className={`size-2 rounded-full ${message.type === 'success' ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
            <p className="text-sm font-medium">{message.text}</p>
          </div>
        )}

        {/* Main Work Area */}
        <div className="glass-card rounded-2xl overflow-hidden border border-zinc-800/50 shadow-2xl">
          <div className="grid lg:grid-cols-12 min-h-[700px]">
            {/* Sidebar */}
            <aside className="lg:col-span-3 border-r border-zinc-800/50 bg-zinc-950/30 p-6 space-y-6">
              <div>
                <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em] mb-4">Configurations</h2>
                <nav className="space-y-1.5">
                  {CONFIG_FILES.map((file) => (
                    <button
                      key={file}
                      onClick={() => setActiveTab(file)}
                      className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all ${
                        activeTab === file
                          ? "bg-accent/10 text-accent border border-accent/20 shadow-inner"
                          : "text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300"
                      }`}
                    >
                      <svg className={`size-4 mr-3 ${activeTab === file ? 'text-accent' : 'text-zinc-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {file.replace('.py', '')}
                    </button>
                  ))}
                </nav>
              </div>

              <div className="pt-6 border-t border-zinc-800/50">
                <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em] mb-4">System Info</h2>
                <div className="bg-zinc-900/50 rounded-xl p-4 space-y-3">
                   <div className="flex justify-between text-[11px]">
                     <span className="text-zinc-500">Status</span>
                     <span className="text-emerald-500 font-bold">ACTIVE</span>
                   </div>
                   <div className="flex justify-between text-[11px]">
                     <span className="text-zinc-500">Auto-Apply</span>
                     <span className="text-zinc-300">ENABLED</span>
                   </div>
                </div>
              </div>

              <div className="pt-6 border-t border-zinc-800/50">
                <button
                  onClick={() => signOut({ callbackUrl: "/login" })}
                  className="w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl text-rose-500 hover:bg-rose-500/10 transition-all border border-transparent hover:border-rose-500/20"
                >
                  <svg className="size-4 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Sign Out
                </button>
              </div>
            </aside>

            {/* Editor Area */}
            <section className="lg:col-span-9 flex flex-col bg-zinc-950/50">
              <div className="flex justify-between items-center p-6 border-b border-zinc-800/50">
                <div className="flex items-center gap-3">
                  <div className="size-2 rounded-full bg-accent"></div>
                  <h2 className="text-lg font-medium text-white flex items-center">
                    Editing <span className="ml-2 font-mono text-xs text-accent bg-accent/5 px-2 py-0.5 rounded border border-accent/10">{activeTab}</span>
                  </h2>
                </div>
                <button
                  onClick={saveConfig}
                  disabled={isSaving || isLoading}
                  className={`inline-flex items-center px-6 py-2 rounded-xl text-sm font-semibold transition-all ${
                    isSaving 
                      ? "bg-zinc-800 text-zinc-600 cursor-not-allowed" 
                      : "bg-white text-zinc-950 hover:bg-zinc-200"
                  }`}
                >
                  {isSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>

              <div className="flex-1 p-6">
                <div className="relative h-full rounded-xl overflow-hidden border border-zinc-800/50 shadow-inner group">
                  <div className="absolute top-0 left-0 w-full h-8 bg-zinc-900 border-b border-zinc-800/50 flex items-center px-4 gap-1.5">
                    <div className="size-2 rounded-full bg-zinc-800"></div>
                    <div className="size-2 rounded-full bg-zinc-800"></div>
                    <div className="size-2 rounded-full bg-zinc-800"></div>
                  </div>
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="w-full h-full min-h-[500px] pt-12 pb-6 px-6 bg-zinc-950/80 text-zinc-300 font-mono text-sm leading-loose resize-none focus:outline-none transition-all cluely-scrollbar"
                    spellCheck="false"
                    placeholder={isLoading ? "Loading configuration..." : "# Your configuration content here"}
                  />
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
