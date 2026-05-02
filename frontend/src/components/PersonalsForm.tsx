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
    <div className="space-y-8 p-1 overflow-y-auto max-h-[600px] scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
      {sections.map((section, idx) => (
        <div key={idx} className="space-y-4">
          <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest border-b border-zinc-800 pb-2">
            {section.title}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {section.fields.map((field) => (
              <div key={field.key} className="space-y-1.5">
                <label className="text-[11px] font-medium text-zinc-400">
                  {field.label}
                </label>
                <input
                  type="text"
                  value={data[field.key] || ""}
                  onChange={(e) => handleChange(field.key, e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                  placeholder={`Enter ${field.label.toLowerCase()}...`}
                />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
