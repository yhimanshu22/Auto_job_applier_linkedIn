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
    <div className="space-y-6 p-1 overflow-y-auto max-h-[550px] scrollbar-thin scrollbar-thumb-zinc-900">
      {/* Profile */}
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Profile Sync
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">LinkedIn URL</label>
            <input
              type="text"
              value={data.linkedIn || ""}
              onChange={(e) => handleChange("linkedIn", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Headline</label>
            <input
              type="text"
              value={data.linkedin_headline || ""}
              onChange={(e) => handleChange("linkedin_headline", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="md:col-span-2 space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Bio Summary</label>
            <textarea
              value={data.linkedin_summary || ""}
              onChange={(e) => handleChange("linkedin_summary", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-blue-600 min-h-[60px]"
            />
          </div>
        </div>
      </div>

      {/* Career */}
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Application Details
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Exp.</label>
            <input
              type="text"
              value={data.years_of_experience || ""}
              onChange={(e) => handleChange("years_of_experience", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Salary</label>
            <input
              type="number"
              value={data.desired_salary || 0}
              onChange={(e) => handleChange("desired_salary", parseInt(e.target.value))}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Notice</label>
            <input
              type="number"
              value={data.notice_period || 0}
              onChange={(e) => handleChange("notice_period", parseInt(e.target.value))}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Visa</label>
            <select
              value={data.require_visa || "No"}
              onChange={(e) => handleChange("require_visa", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none"
            >
              <option>No</option>
              <option>Yes</option>
            </select>
          </div>
        </div>
      </div>

      {/* Cover Letter */}
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Cover Letter Template
        </h3>
        <textarea
          value={data.cover_letter || ""}
          onChange={(e) => handleChange("cover_letter", e.target.value)}
          className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-400 focus:outline-none focus:border-blue-600 min-h-[150px]"
          placeholder="Template content..."
        />
      </div>
    </div>
  );
}
