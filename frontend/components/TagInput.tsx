"use client";

import { useState } from "react";
import type { KeyboardEvent } from "react";

interface TagInputProps {
  id?: string;
  value: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}

/** Chip-style input for free-text list fields (biomarkers, prior treatments, …). */
export default function TagInput({ id, value, onChange, placeholder }: TagInputProps) {
  const [draft, setDraft] = useState("");

  function addTag(raw: string) {
    const tag = raw.trim();
    if (tag && !value.includes(tag)) onChange([...value, tag]);
    setDraft("");
  }

  function removeTag(index: number) {
    onChange(value.filter((_, i) => i !== index));
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(draft);
    } else if (e.key === "Backspace" && draft === "" && value.length > 0) {
      removeTag(value.length - 1);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5 rounded-md border border-zinc-300 bg-white px-2 py-1.5 focus-within:border-zinc-400 focus-within:ring-2 focus-within:ring-zinc-200">
      {value.map((tag, i) => (
        <span
          key={`${tag}-${i}`}
          className="inline-flex items-center gap-1 rounded bg-zinc-100 px-2 py-0.5 text-sm text-zinc-700"
        >
          {tag}
          <button
            type="button"
            onClick={() => removeTag(i)}
            className="text-zinc-400 hover:text-zinc-700"
            aria-label={`Remove ${tag}`}
          >
            ×
          </button>
        </span>
      ))}
      <input
        id={id}
        type="text"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => addTag(draft)}
        placeholder={value.length === 0 ? placeholder : ""}
        className="min-w-[8rem] flex-1 border-0 bg-transparent p-0.5 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none"
      />
    </div>
  );
}
