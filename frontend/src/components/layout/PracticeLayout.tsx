import { Outlet, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon } from 'lucide-react';

export function PracticeLayout() {
  const navigate = useNavigate();

  return (
    <div className="fixed inset-0 bg-background flex flex-col">
      <button
        onClick={() => navigate(-1)}
        className="absolute top-4 left-4 z-10 flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        aria-label="Exit practice"
      >
        <ArrowLeftIcon className="size-4" />
      </button>
      <Outlet />
    </div>
  );
}
