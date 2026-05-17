import { Outlet, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon } from 'lucide-react';

export function PracticeLayout() {
  const navigate = useNavigate();

  return (
    <div className="fixed inset-0 bg-background flex flex-col">
      <button
        onClick={() => navigate(-1)}
        className="absolute top-4 left-4 z-10 flex items-center gap-1.5 text-sm text-navy hover:opacity-70 transition-opacity"
        aria-label="Exit practice"
      >
        <ArrowLeftIcon className="size-4" strokeWidth={2.5} />
      </button>
      <Outlet />
    </div>
  );
}
