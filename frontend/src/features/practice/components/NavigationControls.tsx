import { useEffect } from 'react';
import { ChevronRight } from 'lucide-react';

interface NavigationControlsProps {
  visible: boolean;
  onNext: () => void;
}

export function NavigationControls({ visible, onNext }: NavigationControlsProps) {
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
      className="flex items-center justify-center w-12 h-12 rounded-full bg-navy text-white hover:opacity-80 active:scale-95 transition-all duration-150 shadow-md"
    >
      <ChevronRight className="w-5 h-5" strokeWidth={2.5} />
    </button>
  );
}
