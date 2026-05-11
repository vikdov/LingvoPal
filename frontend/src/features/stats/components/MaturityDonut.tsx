import { useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { VocabMaturity, MaturityKey } from '../types/stats.types';

interface Props {
  data: VocabMaturity | undefined;
  isLoading: boolean;
}

const BUCKET_COLORS: Record<MaturityKey, string> = {
  new: 'var(--chart-1)',
  learning: 'var(--chart-2)',
  young: 'var(--chart-3)',
  mature: 'var(--chart-4)',
  long_term: 'var(--chart-5)',
};

interface TooltipPayloadItem {
  name: string;
  value: number;
  payload: { key: MaturityKey; count: number; range: string };
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayloadItem[] }) {
  if (!active || !payload?.length) return null;
  const { key, count, range } = payload[0].payload;
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 shadow-md font-mono text-xs space-y-0.5">
      <p className="text-foreground font-semibold">{payload[0].name}</p>
      <p className="text-muted-foreground">{range}</p>
      <p className="text-foreground">{count} words · {payload[0].value}%</p>
      {BUCKET_COLORS[key] && <span />}
    </div>
  );
}

export function MaturityDonut({ data, isLoading }: Props) {
  const [expandedKey, setExpandedKey] = useState<MaturityKey | null>(null);

  function toggleBucket(key: MaturityKey) {
    setExpandedKey((prev) => (prev === key ? null : key));
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-foreground">Vocabulary Maturity</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-48 w-full rounded-md" />
        ) : !data || data.total_items === 0 ? (
          <div className="flex items-center justify-center h-48 text-muted-foreground font-mono text-xs">
            No words practiced yet
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-4">
              <div className="shrink-0">
                <ResponsiveContainer width={130} height={130}>
                  <PieChart>
                    <Pie
                      data={data.buckets}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={62}
                      paddingAngle={2}
                      dataKey="percent"
                      nameKey="label"
                    >
                      {data.buckets.map((bucket) => (
                        <Cell key={bucket.key} fill={BUCKET_COLORS[bucket.key]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="flex flex-col gap-1.5 flex-1 min-w-0">
                {data.buckets.map((bucket) => {
                  const isExpanded = expandedKey === bucket.key;
                  const hasWords = bucket.words.length > 0;
                  return (
                    <div key={bucket.key}>
                      <button
                        onClick={() => hasWords && toggleBucket(bucket.key)}
                        className={cn(
                          'flex items-center gap-2 w-full text-left',
                          hasWords && 'cursor-pointer group',
                          !hasWords && 'cursor-default',
                        )}
                        disabled={!hasWords}
                      >
                        <span
                          className="shrink-0 w-2 h-2 rounded-full"
                          style={{ background: BUCKET_COLORS[bucket.key] }}
                        />
                        <span className="font-mono text-[10px] text-muted-foreground w-14 shrink-0">{bucket.label}</span>
                        <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{ width: `${bucket.percent}%`, background: BUCKET_COLORS[bucket.key] }}
                          />
                        </div>
                        <span className="font-mono text-[10px] text-foreground w-7 text-right shrink-0">
                          {bucket.percent > 0 ? `${bucket.percent}%` : '—'}
                        </span>
                        {hasWords && (
                          <ChevronRight
                            className={cn(
                              'size-3 text-muted-foreground transition-transform shrink-0',
                              isExpanded && 'rotate-90',
                            )}
                          />
                        )}
                      </button>

                      {isExpanded && (
                        <div className="mt-1.5 mb-0.5 ml-4 flex flex-wrap gap-1">
                          {bucket.words.map((w) => (
                            <span
                              key={w.item_id}
                              className="inline-flex items-center rounded-md border border-border bg-muted/50 px-2 py-0.5 font-mono text-[10px] text-foreground"
                            >
                              {w.term}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <p className="font-mono text-[10px] text-muted-foreground">
              {data.total_items} words tracked · click bucket to see words
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
