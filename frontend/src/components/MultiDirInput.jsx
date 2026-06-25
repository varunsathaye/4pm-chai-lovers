import React, { useState, useRef } from 'react';
import { X } from 'lucide-react';

export default function MultiDirInput({ values, onChange, label, placeholder }) {
  const [input, setInput] = useState('');
  const inputRef = useRef(null);

  const addValue = (raw) => {
    const trimmed = raw.trim();
    if (trimmed && !values.includes(trimmed)) {
      const next = values.filter(v => v !== '');
      onChange([...next, trimmed]);
    }
  };

  const removeValue = (idx) => {
    const next = values.filter((_, i) => i !== idx);
    onChange(next.length ? next : ['']);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      if (input.includes(',')) {
        input.split(',').forEach(addValue);
      } else {
        addValue(input);
      }
      setInput('');
    }
    if (e.key === 'Backspace' && !input && values.length > 0) {
      removeValue(values.length - 1);
    }
  };

  const handlePaste = (e) => {
    const text = e.clipboardData.getData('text');
    if (text.includes('\n') || text.includes(',')) {
      e.preventDefault();
      const parts = text.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
      const base = values.filter(v => v !== '');
      const next = [...base];
      for (const p of parts) {
        if (p && !next.includes(p)) next.push(p);
      }
      onChange(next.length ? next : ['']);
    }
  };

  const handleBlur = () => {
    if (input.trim()) {
      addValue(input);
      setInput('');
    }
  };

  return (
    <div className="w-full space-y-2">
      <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500 ml-1">{label}</label>
      <div className="flex flex-wrap items-center gap-1.5 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 focus-within:ring-2 focus-within:ring-emerald-500/50 focus-within:border-emerald-500/50 transition-all min-h-[42px]">
        {(values.length === 0 || (values.length === 1 && values[0] === ''))
          ? (
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              onBlur={handleBlur}
              className="flex-1 min-w-[120px] bg-transparent text-zinc-200 outline-none placeholder:text-zinc-700 text-sm py-0.5"
              placeholder={placeholder}
            />
          )
          : (
            <>
              {values.map((v, i) => (
                <span key={i} className="inline-flex items-center gap-1 bg-emerald-500/15 text-emerald-300 text-xs font-medium px-2.5 py-1 rounded-lg border border-emerald-500/20 max-w-full">
                  <span className="truncate">{v}</span>
                  <button
                    type="button"
                    onClick={() => removeValue(i)}
                    className="hover:bg-emerald-500/20 rounded p-0.5 transition-colors shrink-0"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onPaste={handlePaste}
                onBlur={handleBlur}
                className="flex-1 min-w-[100px] bg-transparent text-zinc-200 outline-none placeholder:text-zinc-700 text-sm py-0.5"
                placeholder={values.length ? "Add another…" : placeholder}
              />
            </>
          )
        }
      </div>
    </div>
  );
}
