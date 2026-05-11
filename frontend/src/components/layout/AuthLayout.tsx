import { Outlet } from 'react-router-dom';
import { LingvoLogo } from '@/components/LingvoLogo';

export function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden lg:flex flex-col justify-between bg-primary p-12 text-primary-foreground">
        <LingvoLogo className="h-9 w-auto brightness-0 invert" />
        <div className="space-y-2">
          <p className="text-3xl font-bold">Learn by writing.</p>
          <p className="text-3xl font-bold opacity-60">Not by clicking.</p>
        </div>
        <blockquote className="space-y-1 opacity-70">
          <p className="text-sm italic">
            "The limits of my language mean the limits of my world."
          </p>
          <footer className="text-xs">— Ludwig Wittgenstein</footer>
        </blockquote>
      </div>

      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
