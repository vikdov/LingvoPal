import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { LingvoLogo } from '@/components/LingvoLogo';
import { ToggleTheme } from '@/components/ui/toggle-theme';

export function LandingNav() {
  return (
    <header
      className={cn(
        'sticky top-0 z-50 flex items-center justify-between',
        'px-6 h-12 border-b border-border',
        'backdrop-blur-md bg-background/85',
      )}
    >
      <Link to="/" className="no-underline flex items-center">
        <LingvoLogo className="h-8 w-auto" />
      </Link>

      <div className="flex items-center gap-2">
        <ToggleTheme />

        <Button variant="ghost" size="sm" asChild className="text-muted-foreground hover:text-foreground">
          <Link to="/auth/login">Sign in</Link>
        </Button>

        <Button
          size="sm"
          asChild
          className="font-medium"
          style={{ boxShadow: '0 0 20px -4px rgba(0,105,168,0.55), 0 0 40px -12px rgba(0,105,168,0.3)' }}
        >
          <Link to="/auth/register">Start writing →</Link>
        </Button>
      </div>
    </header>
  );
}
