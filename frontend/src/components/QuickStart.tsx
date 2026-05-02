import React from 'react';

interface QuickStartProps {
  formData: Record<string, any>;
  activeTab: string;
  onClose: () => void;
}

export default function QuickStart({ formData, activeTab, onClose }: QuickStartProps) {
  // Logic to determine completeness based on formData
  const steps = [
    {
      id: 'personals.py',
      label: 'LinkedIn URL & Cookies',
      description: 'Add your profile URL to get started.',
      isDone: !!formData.linkedIn,
    },
    {
      id: 'search.py',
      label: 'Search Filters',
      description: 'Set your target job titles and locations.',
      isDone: Array.isArray(formData.keywords) && formData.keywords.length > 0,
    },
    {
      id: 'questions.py',
      label: 'Application Bio',
      description: 'Complete your bio and headline.',
      isDone: !!formData.linkedin_headline,
    },
    {
      id: 'settings.py',
      label: 'Bot Limits',
      description: 'Review your daily application limits.',
      isDone: !!formData.max_applications_per_day,
    }
  ];

  const completedSteps = steps.filter(s => s.isDone).length;
  const progress = (completedSteps / steps.length) * 100;

  return (
    <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-2xl animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Quick Start Guide</h3>
          <p className="text-xs text-zinc-400 font-medium">Complete these steps to launch the bot.</p>
        </div>
        <button 
          onClick={onClose}
          className="size-6 rounded flex items-center justify-center hover:bg-zinc-900 text-zinc-500 transition-colors"
        >
          <svg className="size-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-[9px] font-bold text-zinc-600 uppercase tracking-tighter">{completedSteps} of {steps.length} completed</span>
          <span className="text-[9px] font-bold text-blue-500">{Math.round(progress)}%</span>
        </div>
        <div className="w-full h-1 bg-zinc-900 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-600 transition-all duration-700"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      <div className="space-y-3">
        {steps.map((step) => (
          <div 
            key={step.id}
            className={`group p-3 rounded-lg border transition-all ${
              step.isDone ? 'bg-zinc-900/20 border-emerald-500/10' : 'bg-zinc-900/50 border-zinc-900'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`size-4 rounded-full mt-0.5 flex items-center justify-center shrink-0 border transition-colors ${
                step.isDone ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-500' : 'bg-zinc-950 border-zinc-800 text-zinc-700'
              }`}>
                {step.isDone ? (
                  <svg className="size-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <div className="size-1 rounded-full bg-zinc-800"></div>
                )}
              </div>
              <div className="flex-1">
                <p className={`text-[11px] font-bold transition-colors ${
                  step.isDone ? 'text-zinc-500' : 'text-zinc-300'
                }`}>
                  {step.label}
                </p>
                <p className="text-[10px] text-zinc-600 leading-tight">
                  {step.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {progress === 100 && (
        <div className="mt-6 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-center">
          <p className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest animate-pulse">
            Ready for Launch!
          </p>
        </div>
      )}
    </div>
  );
}
