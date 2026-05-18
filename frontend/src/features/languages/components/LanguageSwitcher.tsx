import { Globe, Check, ChevronDown, Loader2 } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useUserLanguages, useActivateLanguage } from '../hooks/useUserLanguages';
import { useLanguageStore } from '../store/language.store';

export function LanguageSwitcher() {
  const { data: userLangsData, isLoading } = useUserLanguages();
  const { mutate: activate, isPending } = useActivateLanguage();
  const activeId = useLanguageStore((s) => s.activeLanguageId);
  const clear = useLanguageStore((s) => s.clear);

  const languages = userLangsData?.languages ?? [];

  if (isLoading || !languages.length) return null;

  const active = languages.find((l) => l.language.id === activeId);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground px-2"
          disabled={isPending}
        >
          {isPending ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <Globe className="size-3.5" />
          )}
          <span>{active?.language.name ?? 'All'}</span>
          <ChevronDown className="size-3 opacity-60" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="min-w-[160px]">
        <DropdownMenuLabel className="text-xs text-muted-foreground">
          Learning
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={() => { if (activeId !== null) clear(); }}
          className={cn('text-sm gap-2', activeId === null && 'font-medium')}
        >
          <Check className={cn('size-3.5', activeId === null ? 'opacity-100' : 'opacity-0')} />
          All languages
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {languages.map((l) => (
          <DropdownMenuItem
            key={l.language.id}
            onSelect={() => {
              if (l.language.id !== activeId) activate(l.language.id);
            }}
            className={cn(
              'text-sm gap-2',
              l.language.id === activeId && 'font-medium',
            )}
          >
            <Check
              className={cn(
                'size-3.5',
                l.language.id === activeId ? 'opacity-100' : 'opacity-0',
              )}
            />
            {l.language.name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
