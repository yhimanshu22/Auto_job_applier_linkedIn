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
    <div className="space-y-8 p-1 overflow-y-auto max-h-[600px] scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
      {/* Search Basics */}
      <div className="space-y-4">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest border-b border-zinc-800 pb-2">
          Search Scope
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">Main Search Location</label>
            <input
              type="text"
              value={data.search_location || ""}
              onChange={(e) => handleChange("search_location", e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">Switch Cycle After (n) Jobs</label>
            <input
              type="number"
              value={data.switch_number || 30}
              onChange={(e) => handleChange("switch_number", parseInt(e.target.value))}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50"
            />
          </div>
        </div>
      </div>

      {/* Arrays Section */}
      {[
        { key: "search_terms", label: "Search Terms (Keywords)" },
        { key: "location", label: "Target Locations" },
        { key: "job_title", label: "Preferred Job Titles" }
      ].map((arr) => (
        <div key={arr.key} className="space-y-4">
          <div className="flex justify-between items-center border-b border-zinc-800 pb-2">
            <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
              {arr.label}
            </h3>
            <button 
              onClick={() => addArrayItem(arr.key)}
              className="text-[10px] font-bold text-blue-400 hover:text-blue-300 uppercase tracking-tight"
            >
              + Add Item
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(data[arr.key] || []).map((item: string, idx: number) => (
              <div key={idx} className="relative flex items-center group">
                <input
                  type="text"
                  value={item}
                  onChange={(e) => handleArrayChange(arr.key, idx, e.target.value)}
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg px-4 py-2 text-xs text-zinc-300 focus:outline-none focus:border-blue-500/30"
                />
                <button 
                  onClick={() => removeArrayItem(arr.key, idx)}
                  className="absolute right-2 opacity-0 group-hover:opacity-100 text-red-500/50 hover:text-red-500 p-1"
                >
                  <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Filters */}
      <div className="space-y-4">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest border-b border-zinc-800 pb-2">
          Filters & Booleans
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { key: "under_10_applicants", label: "< 10 Applicants" },
            { key: "security_clearance", label: "Clearance Req." },
            { key: "randomize_search_order", label: "Randomize Order" },
            { key: "pause_after_filters", label: "Pause at Filters" }
          ].map((bool) => (
            <label key={bool.key} className="flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={data[bool.key] || false}
                  onChange={(e) => handleChange(bool.key, e.target.checked)}
                  className="sr-only"
                />
                <div className={`w-8 h-4 rounded-full transition-colors ${data[bool.key] ? 'bg-blue-600' : 'bg-zinc-800'}`}></div>
                <div className={`absolute top-0.5 left-0.5 size-3 bg-white rounded-full transition-transform ${data[bool.key] ? 'translate-x-4' : 'translate-x-0'}`}></div>
              </div>
              <span className="text-[11px] font-medium text-zinc-500 group-hover:text-zinc-300 transition-colors">{bool.label}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
