import { BookOpenIcon, LayersIcon } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useAllLanguages } from '@/features/languages';
import type { SetResponse } from '../types/sets.types';

interface SetCardProps {
  set: SetResponse;
  actions?: React.ReactNode;
  className?: string;
}

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  DRAFT: 'outline',
  COMMUNITY: 'secondary',
  APPROVED: 'default',
  OFFICIAL: 'default',
};

function difficultyLabel(difficulty: number | null): string {
  if (difficulty === null) return 'Any';
  const labels = ['', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'Native'];
  return labels[difficulty] ?? `${difficulty}`;
}

export function SetCard({ set, actions, className }: SetCardProps) {
  const { data: languages = [] } = useAllLanguages();
  const langName = (id: number | null | undefined) =>
    id == null ? '' : (languages.find((l) => l.id === id)?.name ?? String(id));

  return (
    <Card className={cn('h-full', className)}>
      <CardHeader>
        <CardTitle className="line-clamp-2">{set.title}</CardTitle>
        {set.description && (
          <CardDescription className="line-clamp-2">{set.description}</CardDescription>
        )}
      </CardHeader>

      <CardContent className="flex flex-wrap gap-2">
        {set.difficulty !== null && (
          <Badge variant="secondary">{difficultyLabel(set.difficulty)}</Badge>
        )}
        <Badge variant={STATUS_VARIANT[set.status] ?? 'outline'}>{set.status}</Badge>
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <LayersIcon className="size-3" />
          {set.item_count} {set.item_count === 1 ? 'item' : 'items'}
        </span>
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <BookOpenIcon className="size-3" />
          {langName(set.source_lang_id)}{set.target_lang_id != null ? ` → ${langName(set.target_lang_id)}` : ''}
        </span>
      </CardContent>

      {actions && (
        <CardFooter className="gap-2">
          {actions}
        </CardFooter>
      )}
    </Card>
  );
}
