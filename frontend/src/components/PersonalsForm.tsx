import React from 'react';

interface PersonalsFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
}

export default function PersonalsForm({ data, onChange }: PersonalsFormProps) {
  const handleChange = (key: string, value: string) => {
    onChange({ ...data, [key]: value });
  };

  const sections = [
    {
      title: "Basic Information",
      fields: [
        { key: "first_name", label: "First Name" },
        { key: "middle_name", label: "Middle Name" },
        { key: "last_name", label: "Last Name" },
        { key: "email", label: "Email Address" },
        { key: "phone_number", label: "Phone Number" },
      ]
    },
    {
      title: "Location",
      fields: [
        { key: "street", label: "Street" },
        { key: "current_city", label: "City" },
        { key: "state", label: "State/Province" },
        { key: "zipcode", label: "Zip/Postal Code" },
        { key: "country", label: "Country" },
      ]
    },
    {
      title: "Demographics & Status",
      fields: [
        { key: "gender", label: "Gender" },
        { key: "ethnicity", label: "Ethnicity" },
        { key: "disability_status", label: "Disability Status" },
        { key: "veteran_status", label: "Veteran Status" },
      ]
    }
  ];

  return (
    <div className="space-y-6 p-1 overflow-y-auto max-h-[550px] scrollbar-thin scrollbar-thumb-zinc-900">
      {sections.map((section, idx) => (
        <div key={idx} className="space-y-3">
          <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
            {section.title}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
            {section.fields.map((field) => (
              <div key={field.key} className="space-y-1">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">
                  {field.label}
                </label>
                <input
                  type="text"
                  value={data[field.key] || ""}
                  onChange={(e) => handleChange(field.key, e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600 transition-colors"
                  placeholder={`—`}
                />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
