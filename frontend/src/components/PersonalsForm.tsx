import React from "react";

interface PersonalsFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
}

/** Mirrors backend/modules/validator.py validate_personals (+ optional email for forms). */
export default function PersonalsForm({ data, onChange }: PersonalsFormProps) {
  const patch = (key: string, value: any) => onChange({ ...data, [key]: value });

  const ethnicityOptions = [
    "Decline",
    "Hispanic/Latino",
    "American Indian or Alaska Native",
    "Asian",
    "Black or African American",
    "Native Hawaiian or Other Pacific Islander",
    "White",
    "Other",
  ];

  const genderOptions = ["Male", "Female", "Other", "Decline", ""];
  const ynDecline = ["Yes", "No", "Decline"];

  const text = (key: string, label: string, opts?: { placeholder?: string }) => (
    <div key={key} className="space-y-1">
      <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">{label}</label>
      <input
        type="text"
        value={data[key] ?? ""}
        onChange={(e) => patch(key, e.target.value)}
        placeholder={opts?.placeholder}
        className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600 transition-colors"
      />
    </div>
  );

  const select = (key: string, label: string, options: string[]) => (
    <div key={key} className="space-y-1">
      <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">{label}</label>
      <select
        value={data[key] ?? ""}
        onChange={(e) => patch(key, e.target.value)}
        className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
      >
        {options.map((o) => (
          <option key={o || "(empty)"} value={o}>
            {o || "—"}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="space-y-6 p-1 overflow-y-auto max-h-[550px] scrollbar-thin scrollbar-thumb-zinc-900">
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Basic information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          {text("first_name", "First name")}
          {text("middle_name", "Middle name")}
          {text("last_name", "Last name")}
          {text("email", "Email (optional)")}
          {text("phone_number", "Phone number")}
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Location
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          {text("street", "Street")}
          {text("current_city", "City")}
          {text("state", "State / province")}
          {text("zipcode", "Zip / postal code")}
          {text("country", "Country")}
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Demographics (application forms)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          {select("ethnicity", "Ethnicity", ethnicityOptions)}
          {select("gender", "Gender", genderOptions)}
          {select("disability_status", "Disability status", ynDecline)}
          {select("veteran_status", "Veteran status", ynDecline)}
        </div>
      </div>
    </div>
  );
}
