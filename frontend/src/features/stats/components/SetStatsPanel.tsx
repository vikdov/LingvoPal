import { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, BookOpen } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { useSetContext } from '../hooks/useStats';
import type { SetMaturityKey } from '../types/stats.types';

interface Props {
  setId: number;
}

const BUCKET_COLORS: Record<SetMaturityKey, string> = {
  not_started: 'var(--color-muted-foreground)',
  new: 'var(--chart-1)',
  learning: 'var(--chart-2)',
  young: 'var(--chart-3)',
  mature: 'var(--chart-4)',
  long_term: 'var(--chart-5)',
};

export function SetStatsPanel({ setId }: Props) {
  const [open, setOpen] = useState(false);
  const { data, isLoading } = useSetContext(setId);

  // Don't render if no activity at all
  if (!isLoading && data && data.practiced_items === 0) return null;
  if (!isLoading && !data) return null;

  return (
    <Card className="bg-card border-border">
      <button
        className="flex w-full items-center justify-between px-5 py-3 text-left"
        onClick={() => setOpen((v) => !v)}
      >
        <div className="flex items-center gap-2">
          <BookOpen className="size-3.5 text-muted-foreground" />
          <span className="text-sm font-semibold text-foreground">Set Progress</span>
          {data && (
            <span className="font-mono text-[10px] text-muted-foreground">
              {data.practiced_items}/{data.total_items} practiced
            </span>
          )}
        </div>
        {open ? (
          <ChevronUp className="size-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="size-4 text-muted-foreground" />
        )}
      </button>

      {open && (
        <CardContent className="pt-0 pb-5 flex flex-col gap-5">
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-3 w-full rounded-full" />
              <Skeleton className="h-20 w-full rounded-md" />
            </div>
          ) : data ? (
            <>
              {/* Progress bar */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
                    Items practiced
                  </span>
                  <span className="font-mono text-[10px] text-foreground">
                    {data.practiced_items} / {data.total_items} ({data.practiced_percent.toFixed(0)}%)
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${data.practiced_percent}%`,
                      background: 'var(--chart-4)',
                    }}
                  />
                </div>
              </div>

              {/* Maturity stacked bar */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
                  Maturity distribution
                </span>
                <div className="flex h-5 w-full rounded-md overflow-hidden gap-px">
                  {data.maturity_buckets.map((b) =>
                    b.percent > 0 ? (
                      <div
                        key={b.key}
                        className="h-full transition-all duration-500"
                        style={{
                          width: `${b.percent}%`,
                          background: BUCKET_COLORS[b.key],
                          opacity: b.key === 'not_started' ? 0.25 : 1,
                        }}
                        title={`${b.label}: ${b.count} words (${b.percent}%)`}
                      />
                    ) : null
                  )}
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1">
                  {data.maturity_buckets.map((b) =>
                    b.count > 0 ? (
                      <span key={b.key} className="flex items-center gap-1.5 text-[10px] text-foreground/65">
                        <span
                          className="inline-block w-2 h-2 rounded-sm"
                          style={{
                            background: BUCKET_COLORS[b.key],
                            opacity: b.key === 'not_started' ? 0.4 : 1,
                          }}
                        />
                        {b.label} ({b.count})
                      </span>
                    ) : null
                  )}
                </div>
              </div>

              {/* Hardest words */}
              {data.hardest_words.length > 0 && (
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-1.5">
                    <AlertTriangle className="size-3 text-destructive/70" />
                    <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
                      Hardest in this set
                    </span>
                  </div>
                  <div className="flex flex-col divide-y divide-border rounded-md border border-border overflow-hidden">
                    {data.hardest_words.map((w) => (
                      <div key={w.item_id} className="flex items-center justify-between px-3 py-2">
                        <span className="text-sm font-medium text-foreground">{w.term}</span>
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-[10px] text-muted-foreground">
                            {w.total_reviews} reviews
                          </span>
                          <span
                            className={cn(
                              'font-mono text-[10px] font-semibold',
                              w.failure_rate >= 0.6
                                ? 'text-destructive'
                                : w.failure_rate >= 0.4
                                  ? 'text-amber-500'
                                  : 'text-muted-foreground',
                            )}
                          >
                            {(w.failure_rate * 100).toFixed(0)}% fail
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </CardContent>
      )}
    </Card>
  );
}
