import { NavLink } from 'react-router-dom';
import { LayersIcon, SparklesIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

export function DiscoveryTabs() {
  return (
    <div className="flex border-b border-border">
      <NavLink
        to="/sets/discover"
        className={({ isActive }) =>
          cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
            isActive
              ? 'border-primary text-foreground'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border',
          )
        }
      >
        <LayersIcon className="size-4" />
        Sets
      </NavLink>
      <NavLink
        to="/items/discover"
        className={({ isActive }) =>
          cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
            isActive
              ? 'border-primary text-foreground'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border',
          )
        }
      >
        <SparklesIcon className="size-4" />
        Expressions
      </NavLink>
    </div>
  );
}
