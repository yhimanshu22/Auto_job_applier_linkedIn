"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import PersonalsForm from "@/components/PersonalsForm";
import SearchForm from "@/components/SearchForm";
import SettingsForm from "@/components/SettingsForm";
import QuestionsForm from "@/components/QuestionsForm";
import SecretsForm from "@/components/SecretsForm";

const CONFIG_FILES = ["personals.py", "search.py", "settings.py", "questions.py", "secrets.py"];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState(CONFIG_FILES[0]);
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning', text: string } | null>(null);
  const [botStatus, setBotStatus] = useState<"running" | "stopped" | "error" | "paused">("stopped");
  const [appliedCount, setAppliedCount] = useState<number>(0);
  const [applyLimit, setApplyLimit] = useState<number>(0);
  const [botSpeed, setBotSpeed] = useState<number>(5);
  const [resumeName, setResumeName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isBackendHealthy, setIsBackendHealthy] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [subscription, setSubscription] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isFormMode, setIsFormMode] = useState(true);
  const [formData, setFormData] = useState<Record<string, any>>({});
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

    const fetchBotSpeed = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/config/settings");
        const data = await res.json();
        const match = data.content.match(/bot_speed = (\d+)/);
        if (match) setBotSpeed(parseInt(match[1]));
      } catch (err) {}
    };

    checkStatus();
    fetchResumeInfo();
    fetchBotSpeed();
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

  // Live sync: Parse code content into formData whenever content changes
  useEffect(() => {
    if (!content) return;
    
    const parsed: Record<string, any> = {};
    
    // Improved parser using regex to capture key-value pairs even with multi-line strings
    // This looks for "key = value" where value can be a quoted string spanning lines
    const regex = /^([a-zA-Z0-9_]+)\s*=\s*(.*)$/gm;
    let match;
    const rawContent = content;

    // We'll iterate through matches, but for multi-line values, we need a better approach
    // Let's use a simpler but more robust line-by-line with "state"
    const lines = content.split("\n");
    let currentKey = "";
    let currentValue = "";
    let inQuotedString = false;

    lines.forEach((line) => {
      const trimmed = line.trim();

      if (!inQuotedString) {
        if (!trimmed || trimmed.startsWith("#")) return;
        if (line.includes("=")) {
          const [key, ...valParts] = line.split("=");
          currentKey = key.trim();
          let val = valParts.join("=").trim();
          
          if (val.startsWith('"') || val.startsWith("'")) {
            const quote = val[0];
            inQuotedString = true;
            currentValue = val.slice(1);
            
            // Check if it ends on same line
            if (currentValue.endsWith(quote) && currentValue.length > 0) {
              inQuotedString = false;
              parsed[currentKey] = currentValue.slice(0, -1).replace(/\\n/g, "\n");
            }
          } else {
            // Booleans, Numbers, Lists (single line)
            if (val.toLowerCase() === "true") parsed[currentKey] = true;
            else if (val.toLowerCase() === "false") parsed[currentKey] = false;
            else if (!isNaN(Number(val)) && val !== "") parsed[currentKey] = Number(val);
            else if (val.startsWith("[") && val.endsWith("]")) {
              try { parsed[currentKey] = JSON.parse(val.replace(/'/g, '"')); } catch (e) { parsed[currentKey] = val; }
            } else {
              parsed[currentKey] = val;
            }
          }
        }
      } else {
        // We are inside a quoted string
        const quote = content.includes(`${currentKey} = "`) ? '"' : "'";
        if (line.endsWith(quote)) {
          inQuotedString = false;
          currentValue += "\n" + line.slice(0, -1);
          parsed[currentKey] = currentValue.replace(/\\n/g, "\n").replace(/\\"/g, '"');
        } else {
          currentValue += "\n" + line;
        }
      }
    });

    // Final fallback for open strings
    if (inQuotedString && currentKey) {
        parsed[currentKey] = currentValue.replace(/\\n/g, "\n");
    }

    if (JSON.stringify(parsed) !== JSON.stringify(formData)) {
      setFormData(parsed);
    }
  }, [content]);

  // Sync from Form -> Code
  useEffect(() => {
    if (!isFormMode || !activeTab) return;
    
    const category = activeTab.split('.')[0].toUpperCase();
    let newContent = `################ ${category} CONFIGURATION ################\n\n`;
    Object.entries(formData).forEach(([key, value]) => {
      if (typeof value === "string") {
        const escaped = value.replace(/\n/g, "\\n").replace(/"/g, '\\"');
        newContent += `${key} = "${escaped}"\n`;
      } else if (typeof value === "boolean") {
        newContent += `${key} = ${value ? "True" : "False"}\n`;
      } else if (Array.isArray(value)) {
        newContent += `${key} = ${JSON.stringify(value).replace(/"/g, "'")}\n`;
      } else {
        newContent += `${key} = ${value}\n`;
      }
    });
    
    if (newContent !== content) {
      setContent(newContent);
    }
  }, [formData, isFormMode, activeTab]);

  const fetchConfig = async (filename: string) => {
    setIsLoading(true);
    setMessage(null);
    try {
      const cleanName = filename.split('.')[0];
      const res = await fetch(`http://127.0.0.1:8000/api/config/${cleanName}`);
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();
      setContent(data.content || "");
      
      // Parse for form mode
      const parsed: Record<string, any> = {};
      const lines = (data.content || "").split("\n");
      lines.forEach((line: string) => {
        if (line.includes("=") && !line.startsWith("#")) {
          const [key, valStr] = line.split("=").map(s => s.trim());
          let val: any = valStr;
          
          if (valStr.startsWith('"') || valStr.startsWith("'")) {
            val = valStr.replace(/^["']|["']$/g, "").replace(/\\n/g, "\n").replace(/\\"/g, '"');
          } else if (valStr.toLowerCase() === "true") val = true;
          else if (valStr.toLowerCase() === "false") val = false;
          else if (!isNaN(Number(valStr)) && valStr !== "") val = Number(valStr);
          else if (valStr.startsWith("[") && valStr.endsWith("]")) {
            try {
              val = JSON.parse(valStr.replace(/'/g, '"'));
            } catch (e) { val = valStr; }
          }
          parsed[key] = val;
        }
      });
      setFormData(parsed);
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
    let finalContent = content;

    // If we are in form mode, we need to regenerate the content string
    if (isFormMode) {
      const category = activeTab.split('.')[0].toUpperCase();
      finalContent = `################ ${category} CONFIGURATION ################\n\n`;
      Object.entries(formData).forEach(([key, value]) => {
        if (typeof value === "string") {
          const escaped = value.replace(/\n/g, "\\n").replace(/"/g, '\\"');
          finalContent += `${key} = "${escaped}"\n`;
        } else if (typeof value === "boolean") {
          finalContent += `${key} = ${value ? "True" : "False"}\n`;
        } else if (Array.isArray(value)) {
          finalContent += `${key} = ${JSON.stringify(value).replace(/"/g, "'")}\n`;
        } else {
          finalContent += `${key} = ${value}\n`;
        }
      });
    }

    try {
      const cleanName = activeTab.split('.')[0];
      const res = await fetch(`http://127.0.0.1:8000/api/config/${cleanName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: finalContent }),
      });
      if (!res.ok) throw new Error("Failed to save");
      setMessage({ type: 'success', text: 'Configuration saved successfully!' });
      setContent(finalContent);
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

  const updateBotSpeed = async (speed: number) => {
    setBotSpeed(speed);
    try {
        const res = await fetch("http://127.0.0.1:8000/api/config/settings");
        const data = await res.json();
        let newContent = data.content;
        
        if (newContent.includes("bot_speed =")) {
            newContent = newContent.replace(/bot_speed = \d+/, `bot_speed = ${speed}`);
        } else {
            newContent += `\nbot_speed = ${speed}`;
        }

        await fetch("http://127.0.0.1:8000/api/config/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: newContent }),
        });
        
        setMessage({ type: 'success', text: `Speed updated to ${speed}x` });
    } catch (err) {
        setMessage({ type: 'error', text: 'Failed to update speed.' });
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
    <div className="min-h-screen bg-zinc-950 text-zinc-400 font-sans selection:bg-blue-600/20">
      {/* Top Navbar */}
      {/* Slim Navigation */}
      <nav className="sticky top-0 z-[110] bg-zinc-950/80 backdrop-blur-md border-b border-zinc-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-12 items-center">
            <div className="flex items-center gap-4">
              <div className="size-6 rounded bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
                L
              </div>
              <span className="text-sm font-semibold tracking-tight text-white">
                LinkdApply
              </span>
              {subscription && (
                <div className="px-2 py-0.5 rounded border border-zinc-800 bg-zinc-900">
                  <span className={`text-[9px] font-bold uppercase tracking-wider ${
                    subscription.plan === 'pro' ? 'text-indigo-400' :
                    subscription.plan === 'agency' ? 'text-amber-400' :
                    'text-zinc-500'
                  }`}>
                    {subscription.plan}
                  </span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-6">
               <Link 
                  href="/dashboard/billing"
                  className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest hover:text-white transition-colors"
               >
                  Billing
               </Link>
               <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800">
                  <div className={`size-1.5 rounded-full ${isBackendHealthy ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                  <span className="text-[10px] font-medium text-zinc-400 uppercase tracking-tighter">System {isBackendHealthy ? 'OK' : 'Error'}</span>
               </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Confirmation Modal */}
      {/* Confirmation Modal - Minimal */}
      {showConfirm && (
        <div className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 max-w-sm w-full shadow-2xl">
            <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-4">Start Automation</h3>
            
            <div className="space-y-4 mb-6">
              <div className="bg-amber-500/5 border border-amber-500/10 rounded-lg p-3">
                <p className="text-[10px] text-amber-500/80 font-bold uppercase tracking-tight mb-1">Compliance Warning</p>
                <p className="text-[11px] text-zinc-400 leading-relaxed">
                  Ensure your usage complies with LinkedIn's Terms of Service. Automated applications should be reviewed carefully. LinkdApply mimics human patterns, but you are responsible for your account health.
                </p>
              </div>
              <p className="text-[11px] text-zinc-500 leading-relaxed">
                The bot will launch Chrome and begin applying based on your configured limits and settings.
              </p>
            </div>

            <div className="flex gap-2">
              <button 
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2 rounded-lg bg-zinc-900 text-zinc-400 text-[10px] font-bold uppercase tracking-widest hover:text-white transition-colors border border-zinc-800"
              >
                Cancel
              </button>
              <button 
                onClick={startBot}
                className="flex-2 px-6 py-2 rounded-lg bg-blue-600 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-blue-500 transition-all shadow-lg shadow-blue-600/10"
              >
                Start Automation
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

      {/* Minimal Status Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-6 shadow-sm">
          
          <div className="flex items-center gap-4">
            <div className={`size-10 rounded-lg flex items-center justify-center ${
              botStatus === 'running' ? 'bg-blue-600/10 text-blue-500' :
              botStatus === 'error' ? 'bg-red-600/10 text-red-500' :
              'bg-zinc-900 text-zinc-600'
            }`}>
              {botStatus === 'running' ? (
                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                </svg>
              ) : (
                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>
            <div>
              <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-0.5">Process Status</h3>
              <p className="text-lg font-semibold text-white tracking-tight leading-none">
                {botStatus === 'running' ? 'Applying to Jobs' : botStatus === 'error' ? 'Halted' : 'Inactive'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 w-full md:w-auto px-4 py-2 rounded-lg bg-zinc-900/50 border border-zinc-900">
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-lg font-bold text-white tracking-tight">
                  {stats?.monthly_count || 0}
                  <span className="text-zinc-600 text-xs font-medium ml-1">/ {subscription?.limit || '?'}</span>
                </div>
                <div className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest leading-none">Quota Used</div>
              </div>
              <div className="w-24 h-1 bg-zinc-900 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-600 transition-all duration-1000" 
                  style={{ width: `${Math.min(100, (subscription?.limit > 0) ? (stats?.monthly_count / subscription.limit) * 100 : 0)}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            {botStatus === "running" ? (
              <button
                onClick={stopBot}
                disabled={isLoading}
                className="px-4 py-2 rounded-lg bg-red-600 text-white text-xs font-bold uppercase tracking-widest hover:bg-red-500 transition-all disabled:opacity-50"
              >
                Stop
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
                className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-widest transition-all disabled:opacity-50 ${
                  subscription && subscription.status !== 'active' && subscription.status !== 'trialing'
                    ? "bg-zinc-800 text-zinc-500 hover:bg-zinc-700"
                    : "bg-blue-600 text-white hover:bg-blue-500"
                }`}
              >
                Start Automation
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        
        {/* Toast Notification - Minimal */}
        {message && (
          <div className="fixed bottom-6 right-6 z-[100] animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className={`pl-4 pr-2 py-2 rounded-lg flex items-center gap-4 shadow-2xl border backdrop-blur-xl ${
              message.type === 'success' ? 'bg-zinc-950/90 border-emerald-500/20 text-emerald-400' : 
              message.type === 'warning' ? 'bg-zinc-950/90 border-amber-500/20 text-amber-400' :
              'bg-zinc-950/90 border-red-500/20 text-red-400'
            }`}>
              <div className="flex items-center gap-3">
                <div className={`size-1.5 rounded-full animate-pulse ${
                   message.type === 'success' ? 'bg-emerald-500' : 
                   message.type === 'warning' ? 'bg-amber-500' : 'bg-red-500'
                }`}></div>
                <p className="text-[11px] font-medium text-zinc-300 pr-2 border-r border-zinc-800">{message.text}</p>
                <button onClick={() => setMessage(null)} className="size-6 rounded flex items-center justify-center hover:bg-zinc-900 transition-colors">
                  <svg className="size-3 opacity-40 hover:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Layout Grid */}
        <div className="grid lg:grid-cols-12 gap-8">
          
          {/* Left Sidebar - Minimal */}
          <aside className="lg:col-span-3 space-y-4">
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden shadow-sm">
              <div className="px-4 py-2.5 bg-zinc-900/50 border-b border-zinc-900">
                <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Configuration</h3>
              </div>
              <nav className="p-1 space-y-0.5">
                {CONFIG_FILES.map((file) => (
                  <button
                    key={file}
                    onClick={() => setActiveTab(file)}
                    className={`w-full flex items-center px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                      activeTab === file
                        ? "bg-blue-600 text-white font-bold"
                        : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900"
                    }`}
                  >
                    <span className="capitalize">{file.split('.')[0]}</span>
                  </button>
                ))}
              </nav>
            </div>

            <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4 shadow-sm">
              <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3">Settings</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-[10px] font-medium text-zinc-500 uppercase">Bot Speed</span>
                    <span className="text-[10px] font-bold text-blue-500">{botSpeed}x</span>
                  </div>
                  <input 
                    type="range" 
                    min="1" 
                    max="10" 
                    value={botSpeed} 
                    onChange={(e) => updateBotSpeed(parseInt(e.target.value))}
                    className="w-full h-1 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>
              </div>
            </div>

            <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4 shadow-sm">
              <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3">Resume</h3>
              <div className="relative group">
                <input type="file" accept=".pdf" onChange={handleResumeUpload} className="absolute inset-0 size-full opacity-0 cursor-pointer z-10" disabled={isUploading} />
                <div className={`rounded-lg border border-dashed p-3 text-center transition-all ${isUploading ? 'bg-blue-600/5 border-blue-600/30' : 'border-zinc-800 hover:border-zinc-700'}`}>
                  <p className="text-[10px] text-zinc-500 truncate mb-1">{resumeName || "No file"}</p>
                  <span className="text-[9px] font-bold text-blue-500 uppercase tracking-widest">Update</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="w-full py-2 text-[10px] font-bold text-zinc-600 uppercase tracking-widest hover:text-red-500 transition-colors"
            >
              Sign Out
            </button>
          </aside>

          {/* Main Editor Area - Minimal */}
          <section className="lg:col-span-9 flex flex-col h-[650px]">
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden shadow-sm flex flex-col h-full">
              <div className="flex justify-between items-center px-4 py-2 border-b border-zinc-900 bg-zinc-900/30">
                <div className="flex items-center gap-4">
                  <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                    Editor: <span className="text-blue-500 font-mono ml-1 lowercase">{activeTab}</span>
                  </h2>
                  <div className="flex bg-zinc-900 rounded p-0.5">
                    <button onClick={() => setIsFormMode(true)} className={`px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded transition-all ${isFormMode ? 'bg-zinc-800 text-white' : 'text-zinc-600 hover:text-zinc-400'}`}>Form</button>
                    <button onClick={() => setIsFormMode(false)} className={`px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded transition-all ${!isFormMode ? 'bg-zinc-800 text-white' : 'text-zinc-600 hover:text-zinc-400'}`}>Code</button>
                  </div>
                </div>
                <button onClick={saveConfig} disabled={isSaving || isLoading} className="px-3 py-1 bg-blue-600 text-white text-[10px] font-bold uppercase tracking-widest rounded hover:bg-blue-500 transition-all disabled:opacity-50">
                  {isSaving ? "Saving..." : "Save"}
                </button>
              </div>

              <div className="flex-1 relative p-6 overflow-hidden bg-black/20">
                {isFormMode ? (
                  <>
                    {activeTab === "personals.py" && <PersonalsForm data={formData} onChange={setFormData} />}
                    {activeTab === "search.py" && <SearchForm data={formData} onChange={setFormData} />}
                    {activeTab === "settings.py" && <SettingsForm data={formData} onChange={setFormData} />}
                    {activeTab === "questions.py" && <QuestionsForm data={formData} onChange={setFormData} />}
                    {activeTab === "secrets.py" && (
                      <SecretsForm
                        data={formData}
                        onChange={setFormData}
                        isActive={activeTab === "secrets.py"}
                        onAccountsSaved={() => fetchConfig("secrets.py")}
                      />
                    )}
                  </>
                ) : (
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="w-full h-full bg-transparent text-zinc-300 font-mono text-xs leading-loose resize-none focus:outline-none"
                    spellCheck="false"
                  />
                )}
              </div>
            </div>
          </section>
        </div>

        {/* Application History - Minimal */}
        <div className="mt-12 bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 bg-zinc-900/50 border-b border-zinc-900 flex items-center justify-between">
                <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                    Application History
                    <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                </h2>
                <div className="flex gap-4">
                   <div className="text-[9px] font-bold text-zinc-600 uppercase tracking-tight">
                       Applied: <span className="text-zinc-300">{stats?.applied || 0}</span>
                   </div>
                   <div className="text-[9px] font-bold text-zinc-600 uppercase tracking-tight">
                       Failed: <span className="text-zinc-300">{stats?.failed || 0}</span>
                   </div>
                </div>
            </div>
            
            <div className="overflow-x-auto max-h-[400px] scrollbar-thin scrollbar-thumb-zinc-900">
                <table className="w-full text-left">
                  <thead className="sticky top-0 bg-zinc-950 z-10">
                    <tr className="border-b border-zinc-900">
                      <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider">Company</th>
                      <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider">Role</th>
                      <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900">
                    {history.length > 0 ? history.map((app, idx) => (
                      <tr key={idx} className="hover:bg-zinc-900/20 transition-colors">
                        <td className="px-4 py-3">
                          <p className="text-xs font-semibold text-zinc-300">{app.company}</p>
                          <p className="text-[9px] text-zinc-600 uppercase tracking-tighter">
                            {app.timestamp
                              ? new Date(app.timestamp).toLocaleString(undefined, {
                                  dateStyle: "short",
                                  timeStyle: "short",
                                })
                              : ""}
                          </p>
                        </td>
                        <td className="px-4 py-3 text-xs text-zinc-500">{app.job_title}</td>
                        <td className="px-4 py-3 text-right">
                          <span className={`inline-flex px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-tight ${
                            app.status === 'applied' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'
                          }`}>
                            {app.status}
                          </span>
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan={3} className="px-4 py-10 text-center text-zinc-600 text-[10px] uppercase tracking-widest">
                          No recent activity
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
            </div>
        </div>
      </div>
    </div>
  );
}
