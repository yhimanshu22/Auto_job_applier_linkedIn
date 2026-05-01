"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

const CONFIG_FILES = ["personals.py", "search.py", "settings.py", "questions.py"];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState(CONFIG_FILES[0]);
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning', text: string } | null>(null);
  const [botStatus, setBotStatus] = useState<"running" | "stopped" | "error" | "paused">("stopped");
  const [appliedCount, setAppliedCount] = useState<number>(0);
  const [applyLimit, setApplyLimit] = useState<number>(0);
  const [resumeName, setResumeName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isBackendHealthy, setIsBackendHealthy] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [subscription, setSubscription] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const { data: session, status } = useSession();
  const router = useRouter();

  const userId = session?.user?.email || "local-user";

  useEffect(() => {
    fetchConfig(activeTab);
  }, [activeTab]);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/bot/status?user_id=${userId}`);
        if (res.ok) {
          const data = await res.json();
          setBotStatus(data.status);
          if (data.applied_count !== undefined) setAppliedCount(data.applied_count);
          if (data.limit !== undefined) setApplyLimit(data.limit);
          setIsBackendHealthy(true);
        } else {
          setIsBackendHealthy(false);
        }
      } catch (err) {
        setBotStatus("error");
        setIsBackendHealthy(false);
      }
    };

    const fetchResumeInfo = async () => {
        try {
            const res = await fetch("http://127.0.0.1:8000/api/config/questions");
            const data = await res.json();
            const match = data.content.match(/default_resume_path = "(.*)"/);
            if (match) setResumeName(match[1]);
        } catch (err) {}
    };

    const fetchSubscription = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/billing/subscription?user_id=${userId}`);
        if (res.ok) {
          const data = await res.json();
          setSubscription(data);
        }
      } catch (err) {
        console.error("Failed to fetch subscription");
      }
    };

    checkStatus();
    fetchResumeInfo();
    const fetchStats = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/applications/stats?user_id=${userId}`);
        if (res.ok) setStats(await res.json());
      } catch (err) {}
    };

    const fetchHistory = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/applications/history?user_id=${userId}&limit=10`);
        if (res.ok) {
            const data = await res.json();
            setHistory(data.history);
        }
      } catch (err) {}
    };

    if (status === "loading") return;

    checkStatus();
    fetchResumeInfo();
    fetchSubscription();
    fetchStats();
    fetchHistory();
    
    // Poll every 10 seconds
    const statusInterval = setInterval(() => {
      checkStatus();
      fetchSubscription();
      fetchStats();
      fetchHistory();
    }, 10000);
    return () => clearInterval(statusInterval);
  }, [userId, status, router]);

  const fetchConfig = async (filename: string) => {
    setIsLoading(true);
    setMessage(null);
    try {
      const cleanName = filename.split('.')[0];
      const res = await fetch(`http://127.0.0.1:8000/api/config/${cleanName}`);
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();
      setContent(data.content || "");
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Error loading configuration. Ensure backend is running.' });
      setContent("");
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfig = async () => {
    setIsSaving(true);
    setMessage(null);
    try {
      const cleanName = activeTab.split('.')[0];
      const res = await fetch(`http://127.0.0.1:8000/api/config/${cleanName}`, {
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
    setShowConfirm(false);
    if (isLoading) return;
    setIsLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/bot/start`, { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
      });
      if (!res.ok) throw new Error("Failed to start bot");
      setMessage({ type: 'success', text: 'Bot successfully started!' });
      setBotStatus("running");
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Error starting bot.' });
    } finally {
      setIsLoading(false);
    }
  };

  const stopBot = async () => {
    setIsLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/bot/stop`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to stop bot");
      setMessage({ type: 'success', text: 'Bot stopped successfully.' });
      setBotStatus("stopped");
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Error stopping bot.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.type !== "application/pdf") {
        setMessage({ type: 'error', text: 'Please upload a PDF file.' });
        return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("http://127.0.0.1:8000/api/upload/resume", {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error("Upload failed");
        const data = await res.json();
        setResumeName(data.filename);
        setMessage({ type: 'success', text: 'Resume uploaded successfully!' });
    } catch (err) {
        setMessage({ type: 'error', text: 'Failed to upload resume.' });
    } finally {
        setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-zinc-200 font-sans selection:bg-blue-500/30">
      {/* Top Navbar */}
      <nav className="border-b border-zinc-800/50 bg-[#0f172a]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center group cursor-default">
              <div className="size-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-serif font-bold text-xl shadow-lg shadow-blue-500/20">
                L
              </div>
              <span className="ml-3 font-serif text-xl font-semibold tracking-tight text-white transition-colors">
                LinkdApply
              </span>
              {subscription && (
                <div className="ml-4 px-2.5 py-0.5 rounded-full border border-zinc-700/50 bg-zinc-800/50 flex items-center">
                  <span className={`text-[10px] font-bold uppercase tracking-wider ${
                    subscription.plan === 'pro' ? 'text-indigo-400' :
                    subscription.plan === 'agency' ? 'text-amber-400' :
                    'text-zinc-400'
                  }`}>
                    {subscription.plan} Plan
                  </span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-6">
               <Link 
                  href="/dashboard/billing"
                  className="text-xs font-bold text-zinc-400 uppercase tracking-widest hover:text-white transition-colors"
               >
                  Billing
               </Link>
               <div className={`flex items-center gap-3 px-4 py-1.5 rounded-full border ${isBackendHealthy ? 'bg-zinc-900 border-zinc-800' : 'bg-red-500/10 border-red-500/20'}`}>
                  <div className={`size-2 rounded-full ${isBackendHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
                  <span className="text-xs font-medium text-zinc-400">Backend {isBackendHealthy ? 'Online' : 'Offline'}</span>
               </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-[200] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#1e293b] border border-zinc-700 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-2">Start Automation</h3>
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-6">
              <p className="text-sm text-amber-200/90 font-medium leading-relaxed">
                <strong className="text-amber-400">Compliance Warning:</strong> Ensure your usage complies with LinkedIn's Terms of Service. Automated applications should be reviewed carefully. LinkdApply mimics human patterns, but you are responsible for your account health.
              </p>
            </div>
            <p className="text-zinc-400 text-sm mb-6">
              The bot will launch Chrome and begin applying based on your configured limits and settings.
            </p>
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setShowConfirm(false)}
                className="px-5 py-2.5 rounded-xl bg-zinc-800 text-zinc-300 font-medium hover:bg-zinc-700 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={startBot}
                className="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-500 transition-colors shadow-lg shadow-blue-600/20"
              >
                I Agree, Start Bot
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Subscription Banner */}
      {subscription && subscription.status !== 'active' && subscription.status !== 'trialing' && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
          <div className="bg-indigo-600/20 border border-indigo-500/30 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="size-10 bg-indigo-500/20 rounded-full flex items-center justify-center text-indigo-400">
                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h4 className="text-white font-bold">Upgrade to {subscription.plan === 'free' ? 'Start Applying' : 'Reactivate'}</h4>
                <p className="text-sm text-indigo-200/80">You need an active subscription to launch the bot and automate your applications.</p>
              </div>
            </div>
            <Link 
              href="/pricing"
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all shadow-lg shrink-0"
            >
              View Plans
            </Link>
          </div>
        </div>
      )}

      {/* Hero Status Card */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="bg-[#1e293b] border border-zinc-800/80 rounded-3xl p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-8 shadow-2xl shadow-black/20">
          
          <div className="flex items-center gap-6">
            <div className={`size-16 rounded-2xl flex items-center justify-center shadow-lg ${
              botStatus === 'running' ? 'bg-blue-500/20 text-blue-400 shadow-blue-500/10' :
              botStatus === 'error' ? 'bg-red-500/20 text-red-400 shadow-red-500/10' :
              'bg-zinc-800 text-zinc-400 shadow-black/10'
            }`}>
              {botStatus === 'running' ? (
                <svg className="size-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : botStatus === 'error' ? (
                <svg className="size-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : (
                <svg className="size-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className={`size-2 rounded-full ${botStatus === 'running' ? 'bg-blue-500 animate-pulse' : botStatus === 'error' ? 'bg-red-500' : 'bg-zinc-500'}`}></div>
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Bot Status</h3>
              </div>
              <p className="text-3xl font-serif font-medium text-white">
                {botStatus === 'running' ? 'Applying to Jobs...' : botStatus === 'error' ? 'Error Stopped' : 'Ready to Start'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-8 w-full md:w-auto p-5 rounded-2xl bg-black/20 border border-white/5">
            <div className="flex-1 md:w-56">
                <div className="h-3 w-full bg-zinc-900 rounded-full overflow-hidden border border-zinc-800">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-1000 ease-out shadow-[0_0_12px_rgba(59,130,246,0.4)]" 
                    style={{ width: `${Math.min(100, (subscription?.limit > 0) ? (stats?.monthly_count / subscription.limit) * 100 : 0)}%` }}
                  ></div>
                </div>
                <div className="flex justify-between mt-2 text-[11px] font-bold uppercase tracking-wider">
                  <span className="text-zinc-500">Monthly Usage</span>
                  <span className="text-blue-400">{subscription?.limit > 0 ? Math.round((stats?.monthly_count / subscription.limit) * 100) : 0}%</span>
                </div>
            </div>
            <div className="shrink-0 text-right">
                <div className="text-2xl font-bold text-white">{stats?.monthly_count || 0} <span className="text-zinc-500 text-base font-medium">/ {subscription?.limit || '?'}</span></div>
                <div className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest mt-1">Applications this month</div>
            </div>
          </div>

          <div className="flex gap-3">
            {botStatus === "running" ? (
              <button
                onClick={stopBot}
                disabled={isLoading}
                className="inline-flex items-center px-8 py-4 rounded-xl bg-red-500/10 text-red-500 border border-red-500/20 font-semibold shadow-lg hover:bg-red-500/20 transition-all disabled:opacity-50"
              >
                <svg className="size-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" /></svg>
                Stop Process
              </button>
            ) : (
              <button
                onClick={() => {
                  if (subscription && subscription.status !== 'active' && subscription.status !== 'trialing') {
                    window.location.href = '/pricing';
                  } else {
                    setShowConfirm(true);
                  }
                }}
                disabled={isLoading || !isBackendHealthy}
                className={`inline-flex items-center px-8 py-4 rounded-xl font-semibold shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                  subscription && subscription.status !== 'active' && subscription.status !== 'trialing'
                    ? "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
                    : "bg-blue-600 text-white shadow-blue-600/20 hover:bg-blue-500"
                }`}
              >
                {subscription && subscription.status !== 'active' && subscription.status !== 'trialing' ? (
                  <>
                    <svg className="size-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    Upgrade to Launch
                  </>
                ) : (
                  <>
                    <svg className="size-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                    Launch Bot
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        
        {/* Toast Notification */}
        {message && (
          <div className="fixed bottom-8 right-8 z-[100] animate-in fade-in slide-in-from-right-8 duration-500">
            <div className={`p-4 rounded-2xl flex items-center gap-4 shadow-2xl border backdrop-blur-xl ${
              message.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 
              message.type === 'warning' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
              'bg-red-500/10 border-red-500/20 text-red-400'
            }`}>
              <div>
                <p className="text-sm font-bold uppercase tracking-widest opacity-50 mb-0.5">
                  {message.type === 'success' ? 'Success' : message.type === 'warning' ? 'Warning' : 'Error'}
                </p>
                <p className="text-sm font-medium text-white">{message.text}</p>
              </div>
              <button onClick={() => setMessage(null)} className="ml-4 size-8 rounded-lg hover:bg-white/10 flex items-center justify-center transition-colors">
                <svg className="size-4 opacity-40 hover:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Main Layout Grid */}
        <div className="grid lg:grid-cols-12 gap-8">
          
          {/* Left Sidebar (Config Menu & Status) */}
          <aside className="lg:col-span-3 space-y-6">
            <div className="bg-[#1e293b] border border-zinc-800/80 rounded-2xl p-5 shadow-lg">
              <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-4">Configuration Files</h2>
              <nav className="space-y-1">
                {CONFIG_FILES.map((file) => (
                  <button
                    key={file}
                    onClick={() => setActiveTab(file)}
                    className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all ${
                      activeTab === file
                        ? "bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-inner"
                        : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
                    }`}
                  >
                    <svg className={`size-4 mr-3 ${activeTab === file ? 'text-blue-500' : 'text-zinc-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {file.replace('.py', '')}
                  </button>
                ))}
              </nav>
            </div>

            <div className="bg-[#1e293b] border border-zinc-800/80 rounded-2xl p-5 shadow-lg">
              <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-4">Master Resume</h2>
              <div className="relative group">
                  <input 
                      type="file" 
                      accept=".pdf" 
                      onChange={handleResumeUpload}
                      className="absolute inset-0 size-full opacity-0 cursor-pointer z-10"
                      disabled={isUploading}
                  />
                  <div className={`rounded-xl border-2 border-dashed transition-all p-5 text-center ${
                      isUploading ? 'border-blue-500/50 bg-blue-500/5' : 'border-zinc-700 hover:border-blue-500/40 hover:bg-blue-500/5'
                  }`}>
                      {isUploading ? (
                          <div className="flex flex-col items-center gap-2">
                              <div className="size-6 border-2 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                              <span className="text-[10px] text-blue-400 font-bold uppercase tracking-wider mt-2">Uploading...</span>
                          </div>
                      ) : resumeName ? (
                          <div className="flex flex-col items-center gap-2">
                              <div className="size-10 bg-blue-500/10 text-blue-400 rounded-full flex items-center justify-center mb-2">
                                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                              </div>
                              <div className="w-full truncate text-[11px] font-medium text-zinc-300 px-2" title={resumeName}>{resumeName}</div>
                              <span className="text-[9px] uppercase tracking-wider text-zinc-500 font-bold group-hover:text-blue-400 transition-colors mt-1">Click to replace</span>
                          </div>
                      ) : (
                          <div className="flex flex-col items-center gap-2 text-zinc-500">
                              <svg className="size-8 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                              </svg>
                              <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Upload PDF Resume</span>
                          </div>
                      )}
                  </div>
              </div>
            </div>

            <button
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="w-full flex items-center justify-center px-4 py-3 text-sm font-medium rounded-xl text-zinc-400 bg-zinc-900/50 hover:bg-red-500/10 hover:text-red-400 transition-all border border-zinc-800/80 hover:border-red-500/20"
            >
              Sign Out Securely
            </button>
          </aside>

          {/* Main Editor Area */}
          <section className="lg:col-span-9 flex flex-col h-[700px]">
            <div className="bg-[#1e293b] border border-zinc-800/80 rounded-2xl overflow-hidden shadow-2xl flex flex-col h-full">
              
              <div className="flex justify-between items-center p-5 border-b border-zinc-800/80 bg-zinc-900/40">
                <div className="flex items-center gap-3">
                  <h2 className="text-sm font-medium text-white flex items-center uppercase tracking-widest">
                    Editing: <span className="ml-2 font-mono text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md border border-blue-500/20 lowercase">{activeTab}</span>
                  </h2>
                </div>
                <button
                  onClick={saveConfig}
                  disabled={isSaving || isLoading}
                  className={`inline-flex items-center px-5 py-2.5 rounded-lg text-sm font-medium transition-all shadow-sm ${
                    isSaving 
                      ? "bg-zinc-800 text-zinc-500 cursor-not-allowed" 
                      : "bg-blue-600 text-white hover:bg-blue-500 shadow-blue-600/20"
                  }`}
                >
                  {isSaving ? (
                    <><svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-zinc-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Saving...</>
                  ) : "Save Parameters"}
                </button>
              </div>

              <div className="flex-1 relative bg-[#09090b] p-6 overflow-hidden flex flex-col">
                {isLoading && !content ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#09090b]/80 backdrop-blur-sm z-20">
                    <div className="w-48 space-y-4">
                      <div className="h-4 bg-zinc-800 rounded-md animate-pulse"></div>
                      <div className="h-4 bg-zinc-800 rounded-md animate-pulse w-5/6"></div>
                      <div className="h-4 bg-zinc-800 rounded-md animate-pulse w-4/6"></div>
                    </div>
                  </div>
                ) : null}

                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full h-full bg-transparent text-zinc-300 font-mono text-sm leading-loose resize-none focus:outline-none scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent"
                  spellCheck="false"
                  placeholder="# Enter valid Python dictionary configuration..."
                />
              </div>

            </div>
          </section>
        </div>

        {/* Application History Section */}
        <div className="mt-12">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-serif font-medium text-white flex items-center gap-3">
                    Recent Applications
                    <span className="text-xs font-bold bg-zinc-800 text-zinc-400 px-2 py-1 rounded-md border border-zinc-700/50 uppercase tracking-widest">Live Updates</span>
                </h2>
                <div className="flex gap-4">
                   <div className="flex items-center gap-2 text-xs font-medium text-emerald-400">
                       <div className="size-1.5 rounded-full bg-emerald-500"></div>
                       {stats?.applied || 0} Applied
                   </div>
                   <div className="flex items-center gap-2 text-xs font-medium text-amber-400">
                       <div className="size-1.5 rounded-full bg-amber-500"></div>
                       {stats?.skipped || 0} Skipped
                   </div>
                   <div className="flex items-center gap-2 text-xs font-medium text-red-400">
                       <div className="size-1.5 rounded-full bg-red-500"></div>
                       {stats?.failed || 0} Failed
                   </div>
                </div>
            </div>
            
            <div className="bg-[#1e293b] border border-zinc-800/80 rounded-2xl overflow-hidden shadow-xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-zinc-900/40 border-b border-zinc-800/80">
                                <th className="px-6 py-4 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Time</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Company</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Job Title</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Status</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800/50">
                            {history.length > 0 ? history.map((app) => (
                                <tr key={app.id} className="hover:bg-zinc-800/30 transition-colors group">
                                    <td className="px-6 py-4 text-xs text-zinc-500 font-mono">
                                        {new Date(app.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm font-bold text-white group-hover:text-blue-400 transition-colors">{app.company}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-xs text-zinc-400 max-w-xs truncate">{app.job_title}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                                            app.status === 'applied' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                            app.status === 'skipped' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                            'bg-red-500/10 text-red-400 border-red-500/20'
                                        }`}>
                                            {app.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <a 
                                            href={app.job_url} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="text-xs font-bold text-zinc-600 hover:text-white transition-colors"
                                        >
                                            View Job
                                        </a>
                                    </td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-zinc-500 text-sm italic">
                                        No recent activity. Start the bot to see applications here.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
