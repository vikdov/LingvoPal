import { useState, useRef, useEffect } from 'react';
import { Brain } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Option {
  value: number;
  label: string;
  color: string;
}

const OPTIONS: Option[] = [
  { value: 1, label: 'Blackout', color: 'text-destructive' },
  { value: 2, label: 'Hard', color: 'text-orange-500' },
  { value: 4, label: 'Good', color: 'text-emerald-500' },
  { value: 5, label: 'Easy', color: 'text-primary' },
];

interface ConfidenceOverrideMenuProps {
  itemId: number;
  current: number | null;
  onSelect: (itemId: number, value: number | null) => void;
}

export function ConfidenceOverrideMenu({ itemId, current, onSelect }: ConfidenceOverrideMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  const selected = OPTIONS.find((o) => o.value === current);

  function handleSelect(value: number) {
    // Toggle off if same option clicked again
    onSelect(itemId, current === value ? null : value);
    setOpen(false);
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Override confidence"
        className={cn(
          'flex items-center gap-1.5 px-2 py-1 rounded-md text-xs transition-all duration-150',
          'border border-transparent hover:border-border hover:bg-muted',
          selected ? 'text-muted-foreground' : 'text-muted-foreground/40 hover:text-muted-foreground',
        )}
      >
        <Brain className={cn('w-3.5 h-3.5', selected ? selected.color : '')} />
        {selected && <span className={cn('font-medium', selected.color)}>{selected.label}</span>}
      </button>

      {open && (
        <div className={cn(
          'absolute bottom-full mb-1.5 left-0',
          'flex flex-col gap-0.5 p-1 min-w-[6.5rem]',
          'bg-popover border border-border rounded-lg shadow-md',
          'z-50',
        )}>
          {OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleSelect(opt.value)}
              className={cn(
                'flex items-center gap-2 px-2.5 py-1.5 rounded-md text-xs text-left transition-colors',
                'hover:bg-accent',
                current === opt.value ? 'bg-accent' : '',
                opt.color,
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
