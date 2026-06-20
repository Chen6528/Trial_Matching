"use client";

import type { PatientFormValues } from "@/lib/schema";

type LabRow = PatientFormValues["lab_values"][number];

interface KeyValueInputProps {
  value: LabRow[];
  onChange: (next: LabRow[]) => void;
}

const cellClass =
  "w-full rounded-md border border-zinc-300 bg-white px-2.5 py-1.5 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200";

/** Dynamic key/value rows that map to the `lab_values` dict. */
export default function KeyValueInput({ value, onChange }: KeyValueInputProps) {
  function update(index: number, patch: Partial<LabRow>) {
    onChange(value.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  }

  function addRow() {
    onChange([...value, { key: "", value: "" }]);
  }

  function removeRow(index: number) {
    onChange(value.filter((_, i) => i !== index));
  }

  return (
    <div className="space-y-2">
      {value.map((row, i) => (
        <div key={i} className="flex items-center gap-2">
          <input
            value={row.key}
            onChange={(e) => update(i, { key: e.target.value })}
            placeholder="Label (e.g. eGFR)"
            className={cellClass}
          />
          <input
            value={row.value}
            onChange={(e) => update(i, { value: e.target.value })}
            placeholder="Value (e.g. 78 mL/min)"
            className={cellClass}
          />
          <button
            type="button"
            onClick={() => removeRow(i)}
            className="shrink-0 rounded-md px-2 py-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700"
            aria-label="Remove lab value"
          >
            ×
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addRow}
        className="text-sm font-medium text-zinc-600 hover:text-zinc-900"
      >
        + Add lab value
      </button>
    </div>
  );
}
