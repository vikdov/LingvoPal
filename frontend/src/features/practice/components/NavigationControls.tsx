import { useEffect } from 'react';
import { ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavigationControlsProps {
  visible: boolean;
  onNext: () => void;
}

export function NavigationControls({ visible, onNext }: NavigationControlsProps) {
  // Keyboard ownership rule: when input is not active (lifecycle resolved),
  // Enter here advances to the next item. Input's own keydown stops propagation
  // so these two handlers never fire simultaneously.
  useEffect(() => {
    if (!visible) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Enter') {
        e.preventDefault();
        onNext();
      }
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [visible, onNext]);

  return (
    <button
      onClick={onNext}
      aria-label="Next expression"
      className={cn(
        'flex items-center justify-center w-12 h-12 rounded-full transition-all duration-200',
        'bg-foreground text-background shadow-md hover:opacity-80 active:scale-95',
        visible ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
      )}
    >
      <ChevronRight className="w-5 h-5" />
    </button>
  );
}
