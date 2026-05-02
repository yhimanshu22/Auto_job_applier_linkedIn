import React from 'react';

interface QuestionsFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
}

export default function QuestionsForm({ data, onChange }: QuestionsFormProps) {
  const handleChange = (key: string, value: any) => {
    onChange({ ...data, [key]: value });
  };

  return (
    <div className="space-y-8 p-1 overflow-y-auto max-h-[600px] scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
      {/* Resume & Profile */}
      <div className="space-y-4">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest border-b border-zinc-800 pb-2">
          LinkedIn Profile Sync
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">LinkedIn URL</label>
            <input
              type="text"
              value={data.linkedIn || ""}
              onChange={(e) => handleChange("linkedIn", e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">Headline</label>
            <input
              type="text"
              value={data.linkedin_headline || ""}
              onChange={(e) => handleChange("linkedin_headline", e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50"
            />
          </div>
          <div className="md:col-span-2 space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">AI Summary (Bio)</label>
            <textarea
              value={data.linkedin_summary || ""}
              onChange={(e) => handleChange("linkedin_summary", e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 min-h-[80px]"
            />
          </div>
        </div>
      </div>

      {/* Career Details */}
      <div className="space-y-4">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest border-b border-zinc-800 pb-2">
          Job Application Details
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">Years Exp.</label>
            <input
              type="text"
              value={data.years_of_experience || ""}
              onChange={(e) => handleChange("years_of_experience", e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">Desired Salary</label>
            <input
              type="number"
              value={data.desired_salary || 0}
              onChange={(e) => handleChange("desired_salary", parseInt(e.target.value))}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">Notice Period</label>
            <input
              type="number"
              value={data.notice_period || 0}
              onChange={(e) => handleChange("notice_period", parseInt(e.target.value))}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">Visa Required?</label>
            <select
              value={data.require_visa || "No"}
              onChange={(e) => handleChange("require_visa", e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none"
            >
              <option>No</option>
              <option>Yes</option>
            </select>
          </div>
        </div>
      </div>

      {/* Cover Letter */}
      <div className="space-y-4">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest border-b border-zinc-800 pb-2">
          Cover Letter Template
        </h3>
        <div className="space-y-1.5">
          <textarea
            value={data.cover_letter || ""}
            onChange={(e) => handleChange("cover_letter", e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm font-serif text-white focus:outline-none focus:border-blue-500/50 min-h-[200px]"
            placeholder="Write your cover letter template here..."
          />
          <p className="text-[10px] text-zinc-500 italic">This template is used by the AI to generate tailored cover letters if your plan supports it.</p>
        </div>
      </div>
    </div>
  );
}
