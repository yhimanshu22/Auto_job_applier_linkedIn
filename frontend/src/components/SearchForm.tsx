import React from "react";

interface SearchFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
}

/** Mirrors backend/modules/validator.py validate_search — same keys as DB / pseudo-python export. */
export default function SearchForm({ data, onChange }: SearchFormProps) {
  const patch = (key: string, value: any) => onChange({ ...data, [key]: value });

  const handleArrayChange = (key: string, index: number, value: string) => {
    const arr = [...(data[key] || [])];
    arr[index] = value;
    patch(key, arr);
  };

  const addArrayItem = (key: string) => patch(key, [...(data[key] || []), ""]);

  const removeArrayItem = (key: string, index: number) => {
    patch(
      key,
      (data[key] || []).filter((_: unknown, i: number) => i !== index)
    );
  };

  const multiToggle = (key: string, option: string, allowed: string[]) => {
    const cur: string[] = Array.isArray(data[key]) ? [...data[key]] : [];
    const next = cur.includes(option) ? cur.filter((x) => x !== option) : [...cur, option];
    patch(key, next.filter((x) => allowed.includes(x)));
  };

  const ArrayBlock = ({
    arrKey,
    label,
    hint,
  }: {
    arrKey: string;
    label: string;
    hint?: string;
  }) => (
    <div className="space-y-3">
      <div className="flex justify-between items-center border-b border-zinc-900 pb-1.5">
        <div>
          <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">{label}</h3>
          {hint && <p className="text-[9px] text-zinc-600 mt-0.5">{hint}</p>}
        </div>
        <button
          type="button"
          onClick={() => addArrayItem(arrKey)}
          className="text-[9px] font-bold text-blue-600 hover:text-blue-500 uppercase tracking-tighter"
        >
          + Add
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {(data[arrKey] || []).map((item: string, idx: number) => (
          <div key={idx} className="relative flex items-center group">
            <input
              type="text"
              value={item}
              onChange={(e) => handleArrayChange(arrKey, idx, e.target.value)}
              className="w-full bg-zinc-950/50 border border-zinc-900 rounded px-3 py-1 text-[11px] text-zinc-400 focus:outline-none focus:border-blue-600/50"
              placeholder="…"
            />
            <button
              type="button"
              onClick={() => removeArrayItem(arrKey, idx)}
              className="absolute right-1.5 opacity-0 group-hover:opacity-100 text-red-500/40 hover:text-red-500 p-0.5"
            >
              <svg className="size-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );

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
      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter group-hover:text-zinc-300">
        {label}
      </span>
    </label>
  );

  const experienceOpts = [
    "Internship",
    "Entry level",
    "Associate",
    "Mid-Senior level",
    "Director",
    "Executive",
  ];
  const jobTypeOpts = [
    "Full-time",
    "Part-time",
    "Contract",
    "Temporary",
    "Volunteer",
    "Internship",
    "Other",
  ];
  const onSiteOpts = ["On-site", "Remote", "Hybrid"];

  const MultiChip = (key: string, options: string[], label: string) => (
    <div className="space-y-2">
      <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight block">{label}</label>
      <div className="flex flex-wrap gap-1.5">
        {options.map((opt) => {
          const on = (Array.isArray(data[key]) ? data[key] : []).includes(opt);
          return (
            <button
              key={opt}
              type="button"
              onClick={() => multiToggle(key, opt, options)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium border transition-colors ${
                on
                  ? "bg-blue-600/20 border-blue-600/50 text-blue-300"
                  : "bg-zinc-950 border-zinc-800 text-zinc-500 hover:border-zinc-700"
              }`}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="space-y-8 p-1 overflow-y-auto max-h-[550px] scrollbar-thin scrollbar-thumb-zinc-900">
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Search scope
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          <div className="space-y-1 md:col-span-2">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Main search location</label>
            <input
              type="text"
              value={data.search_location ?? ""}
              onChange={(e) => patch("search_location", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
              placeholder="e.g. United States"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Switch after (n) jobs</label>
            <input
              type="number"
              min={1}
              value={data.switch_number ?? 30}
              onChange={(e) => patch("switch_number", parseInt(e.target.value, 10) || 1)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Salary filter text</label>
            <input
              type="text"
              value={data.salary ?? ""}
              onChange={(e) => patch("salary", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
              placeholder='e.g. "$100,000+"'
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Sort by</label>
            <select
              value={data.sort_by ?? ""}
              onChange={(e) => patch("sort_by", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            >
              <option value="">Default</option>
              <option value="Most recent">Most recent</option>
              <option value="Most relevant">Most relevant</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Date posted</label>
            <select
              value={data.date_posted ?? ""}
              onChange={(e) => patch("date_posted", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            >
              <option value="">Any time</option>
              <option value="Past month">Past month</option>
              <option value="Past week">Past week</option>
              <option value="Past 24 hours">Past 24 hours</option>
            </select>
          </div>
          <div className="flex flex-wrap gap-4 md:col-span-2 pt-1">
            <Toggle k="randomize_search_order" label="Randomize search order" />
            <Toggle k="easy_apply_only" label="Easy Apply only" />
            <Toggle k="pause_after_filters" label="Pause after filters" />
          </div>
        </div>
      </div>

      <ArrayBlock arrKey="search_terms" label="Search terms (keywords)" hint="Maps to search_terms in config." />

      <ArrayBlock arrKey="location" label="Additional locations" />

      <ArrayBlock arrKey="job_titles" label="Job titles" hint="Config key: job_titles" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {MultiChip("experience_level", experienceOpts, "Experience level")}
        {MultiChip("job_type", jobTypeOpts, "Job type")}
        {MultiChip("on_site", onSiteOpts, "Workplace (on-site / remote / hybrid)")}
      </div>

      <ArrayBlock arrKey="companies" label="Companies (filter)" />
      <ArrayBlock arrKey="industry" label="Industries" />
      <ArrayBlock arrKey="job_function" label="Job function" />
      <ArrayBlock arrKey="benefits" label="Benefits" />
      <ArrayBlock arrKey="commitments" label="Commitments" />

      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Word filters (lists of strings)
        </h3>
        <ArrayBlock arrKey="bad_words" label="Bad words (skip job)" />
        <ArrayBlock arrKey="about_company_bad_words" label="Bad words in About company" />
        <ArrayBlock arrKey="about_company_good_words" label="Good words in About company" />
      </div>

      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Other filters
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Toggle k="under_10_applicants" label="< 10 applicants" />
          <Toggle k="in_your_network" label="In your network" />
          <Toggle k="fair_chance_employer" label="Fair chance employer" />
          <Toggle k="security_clearance" label="Security clearance" />
          <Toggle k="did_masters" label="Master's filter" />
        </div>
        <div className="space-y-1 max-w-xs">
          <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">
            Current experience (years, −1 = any)
          </label>
          <input
            type="number"
            value={data.current_experience ?? -1}
            onChange={(e) => patch("current_experience", parseInt(e.target.value, 10))}
            className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
          />
        </div>
      </div>
    </div>
  );
}
