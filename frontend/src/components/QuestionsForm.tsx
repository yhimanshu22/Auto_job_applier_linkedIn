import React from "react";

interface QuestionsFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
}

/** Mirrors backend/modules/validator.py validate_questions. */
export default function QuestionsForm({ data, onChange }: QuestionsFormProps) {
  const patch = (key: string, value: any) => onChange({ ...data, [key]: value });

  const citizenshipOpts = [
    "U.S. Citizen/Permanent Resident",
    "Non-citizen allowed to work for any employer",
    "Non-citizen allowed to work for current employer",
    "Non-citizen seeking work authorization",
    "Canadian Citizen/Permanent Resident",
    "Other",
  ];

  const Toggle = ({ k, label }: { k: string; label: string }) => (
    <label className="flex items-center gap-2 cursor-pointer group">
      <div className="relative">
        <input
          type="checkbox"
          checked={!!data[k]}
          onChange={(e) => patch(k, e.target.checked)}
          className="sr-only"
        />
        <div className={`w-6 h-3 rounded-full transition-colors ${data[k] ? "bg-blue-600" : "bg-zinc-900"}`} />
        <div
          className={`absolute top-0.5 left-0.5 size-2 bg-white rounded-full transition-transform ${
            data[k] ? "translate-x-3" : "translate-x-0"
          }`}
        />
      </div>
      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter">{label}</span>
    </label>
  );

  return (
    <div className="space-y-8 p-1 overflow-y-auto max-h-[550px] scrollbar-thin scrollbar-thumb-zinc-900">
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Resume & links
        </h3>
        <div className="grid grid-cols-1 gap-3">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Default resume filename</label>
            <input
              type="text"
              value={data.default_resume_path ?? ""}
              onChange={(e) => patch("default_resume_path", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
              placeholder="resume.pdf"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">LinkedIn URL</label>
              <input
                type="text"
                value={data.linkedIn ?? ""}
                onChange={(e) => patch("linkedIn", e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Website / portfolio</label>
              <input
                type="text"
                value={data.website ?? ""}
                onChange={(e) => patch("website", e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Profile text for applications
        </h3>
        <div className="grid grid-cols-1 gap-3">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">LinkedIn headline</label>
            <input
              type="text"
              value={data.linkedin_headline ?? ""}
              onChange={(e) => patch("linkedin_headline", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">LinkedIn summary / bio</label>
            <textarea
              value={data.linkedin_summary ?? ""}
              onChange={(e) => patch("linkedin_summary", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-blue-600 min-h-[80px]"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Cover letter template</label>
            <textarea
              value={data.cover_letter ?? ""}
              onChange={(e) => patch("cover_letter", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-400 focus:outline-none focus:border-blue-600 min-h-[120px]"
            />
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Compensation & status
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Years of experience (text)</label>
            <input
              type="text"
              value={data.years_of_experience ?? ""}
              onChange={(e) => patch("years_of_experience", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
              placeholder='e.g. "5+"'
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Desired salary (number)</label>
            <input
              type="number"
              value={data.desired_salary ?? 0}
              onChange={(e) => patch("desired_salary", parseInt(e.target.value, 10) || 0)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Current CTC (number)</label>
            <input
              type="number"
              value={data.current_ctc ?? 0}
              onChange={(e) => patch("current_ctc", parseInt(e.target.value, 10) || 0)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Notice period (days)</label>
            <input
              type="number"
              value={data.notice_period ?? 0}
              onChange={(e) => patch("notice_period", parseInt(e.target.value, 10) || 0)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1 md:col-span-2">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Recent employer</label>
            <input
              type="text"
              value={data.recent_employer ?? ""}
              onChange={(e) => patch("recent_employer", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Require visa sponsorship</label>
            <select
              value={data.require_visa ?? "No"}
              onChange={(e) => patch("require_visa", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            >
              <option>No</option>
              <option>Yes</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">US / work authorization</label>
            <select
              value={data.us_citizenship ?? citizenshipOpts[0]}
              onChange={(e) => patch("us_citizenship", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            >
              {citizenshipOpts.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1 md:col-span-2">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">
              Confidence (e.g. scale 1–10 text)
            </label>
            <input
              type="text"
              value={data.confidence_level ?? ""}
              onChange={(e) => patch("confidence_level", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Apply flow
        </h3>
        <div className="flex flex-wrap gap-6">
          <Toggle k="pause_before_submit" label="Pause before submit" />
          <Toggle k="pause_at_failed_question" label="Pause at failed question" />
          <Toggle k="overwrite_previous_answers" label="Overwrite previous answers" />
        </div>
      </div>
    </div>
  );
}
