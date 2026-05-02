import React from 'react';

interface SearchFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
}

export default function SearchForm({ data, onChange }: SearchFormProps) {
  const handleChange = (key: string, value: any) => {
    onChange({ ...data, [key]: value });
  };

  const handleArrayChange = (key: string, index: number, value: string) => {
    const newArray = [...(data[key] || [])];
    newArray[index] = value;
    handleChange(key, newArray);
  };

  const addArrayItem = (key: string) => {
    handleChange(key, [...(data[key] || []), ""]);
  };

  const removeArrayItem = (key: string, index: number) => {
    const newArray = (data[key] || []).filter((_: any, i: number) => i !== index);
    handleChange(key, newArray);
  };

  return (
    <div className="space-y-6 p-1 overflow-y-auto max-h-[550px] scrollbar-thin scrollbar-thumb-zinc-900">
      {/* Search Basics */}
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Search Scope
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Main Search Location</label>
            <input
              type="text"
              value={data.search_location || ""}
              onChange={(e) => handleChange("search_location", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
              placeholder="e.g. Remote"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Switch After (n) Jobs</label>
            <input
              type="number"
              value={data.switch_number || 30}
              onChange={(e) => handleChange("switch_number", parseInt(e.target.value))}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
        </div>
      </div>

      {/* Arrays Section */}
      {[
        { key: "search_terms", label: "Keywords" },
        { key: "location", label: "Target Locations" },
        { key: "job_title", label: "Job Titles" }
      ].map((arr) => (
        <div key={arr.key} className="space-y-3">
          <div className="flex justify-between items-center border-b border-zinc-900 pb-1.5">
            <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">
              {arr.label}
            </h3>
            <button 
              onClick={() => addArrayItem(arr.key)}
              className="text-[9px] font-bold text-blue-600 hover:text-blue-500 uppercase tracking-tighter"
            >
              + Add
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {(data[arr.key] || []).map((item: string, idx: number) => (
              <div key={idx} className="relative flex items-center group">
                <input
                  type="text"
                  value={item}
                  onChange={(e) => handleArrayChange(arr.key, idx, e.target.value)}
                  className="w-full bg-zinc-950/50 border border-zinc-900 rounded px-3 py-1 text-[11px] text-zinc-400 focus:outline-none focus:border-blue-600/50"
                  placeholder="Item..."
                />
                <button 
                  onClick={() => removeArrayItem(arr.key, idx)}
                  className="absolute right-1.5 opacity-0 group-hover:opacity-100 text-red-500/40 hover:text-red-500 p-0.5"
                >
                  <svg className="size-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Filters */}
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Filters
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { key: "under_10_applicants", label: "< 10 Apps" },
            { key: "security_clearance", label: "Clearance" },
            { key: "randomize_search_order", label: "Randomize" },
            { key: "pause_after_filters", label: "Pause" }
          ].map((bool) => (
            <label key={bool.key} className="flex items-center gap-2 cursor-pointer group">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={data[bool.key] || false}
                  onChange={(e) => handleChange(bool.key, e.target.checked)}
                  className="sr-only"
                />
                <div className={`w-6 h-3 rounded-full transition-colors ${data[bool.key] ? 'bg-blue-600' : 'bg-zinc-900'}`}></div>
                <div className={`absolute top-0.5 left-0.5 size-2 bg-white rounded-full transition-transform ${data[bool.key] ? 'translate-x-3' : 'translate-x-0'}`}></div>
              </div>
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter group-hover:text-zinc-300">{bool.label}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
