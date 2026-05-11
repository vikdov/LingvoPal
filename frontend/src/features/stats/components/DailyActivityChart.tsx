import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { RangeStats } from '../types/stats.types';

interface Props {
  data: RangeStats | undefined;
  selectedDays: number;
  onDaysChange: (days: number) => void;
  isLoading: boolean;
}

const RANGES = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
] as const;

function buildSeries(data: RangeStats | undefined, days: number) {
  const map = new Map<string, { correct: number; incorrect: number; new_words: number }>();
  if (data) {
    for (const d of data.daily) {
      map.set(d.stat_date, {
        correct: d.correct_count,
        incorrect: d.incorrect_count,
        new_words: d.new_words_count,
      });
    }
  }
  const series: { date: string; label: string; correct: number; incorrect: number; new_words: number }[] = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const iso = d.toISOString().slice(0, 10);
    const entry = map.get(iso);
    const label = d.toLocaleDateString('en-US', days <= 7 ? { weekday: 'short' } : { month: 'short', day: 'numeric' });
    series.push({
      date: iso,
      label,
      correct: entry?.correct ?? 0,
      incorrect: entry?.incorrect ?? 0,
      new_words: entry?.new_words ?? 0,
    });
  }
  return series;
}

interface TooltipPayloadItem {
  name: string;
  value: number;
  color: string;
}

function CustomTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const correct = payload.find((p) => p.name === 'correct')?.value ?? 0;
  const incorrect = payload.find((p) => p.name === 'incorrect')?.value ?? 0;
  const newWords = payload.find((p) => p.name === 'new_words')?.value ?? 0;
  const total = correct + incorrect;
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 shadow-md font-mono text-xs space-y-0.5">
      <p className="text-muted-foreground mb-1">{label}</p>
      {total > 0 ? (
        <>
          <p className="text-foreground">{total} reviews total</p>
          <p style={{ color: 'var(--chart-4)' }}>{correct} correct</p>
          {incorrect > 0 && <p style={{ color: 'var(--destructive)' }}>{incorrect} incorrect</p>}
          {newWords > 0 && <p style={{ color: 'var(--chart-1)' }}>{newWords} new</p>}
        </>
      ) : (
        <p className="text-muted-foreground">No activity</p>
      )}
    </div>
  );
}

export function DailyActivityChart({ data, selectedDays, onDaysChange, isLoading }: Props) {
  const series = buildSeries(data, selectedDays);

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-4">
          <CardTitle className="text-sm font-semibold text-foreground">Daily Activity</CardTitle>
          <div className="flex items-center gap-1">
            {RANGES.map(({ label, days }) => (
              <button
                key={days}
                onClick={() => onDaysChange(days)}
                className={cn(
                  'px-2.5 py-1 rounded-md font-mono text-[10px] uppercase tracking-wider transition-colors',
                  selectedDays === days
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-48 w-full rounded-md" />
        ) : (
          <>
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={series} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="var(--border)" strokeOpacity={0.6} />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 9, fontFamily: 'var(--font-mono)', fill: 'var(--color-muted-foreground)' }}
                  tickLine={false}
                  axisLine={false}
                  interval={selectedDays <= 7 ? 0 : selectedDays <= 30 ? 6 : 13}
                />
                <YAxis
                  tick={{ fontSize: 9, fontFamily: 'var(--font-mono)', fill: 'var(--color-muted-foreground)' }}
                  tickLine={false}
                  axisLine={false}
                  allowDecimals={false}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--color-muted)', opacity: 0.4 }} />
                <Bar dataKey="correct" name="correct" stackId="reviews" fill="var(--chart-4)" radius={[0, 0, 0, 0]} maxBarSize={32} />
                <Bar dataKey="incorrect" name="incorrect" stackId="reviews" fill="var(--destructive)" fillOpacity={0.45} radius={[3, 3, 0, 0]} maxBarSize={32} />
                <Line
                  dataKey="new_words"
                  name="new_words"
                  type="monotone"
                  stroke="var(--chart-1)"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 3 }}
                />
              </ComposedChart>
            </ResponsiveContainer>

            <div className="flex items-center gap-4 mt-3 flex-wrap">
              <span className="flex items-center gap-1.5 font-mono text-[10px] text-muted-foreground">
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: 'var(--chart-4)' }} />
                correct
              </span>
              <span className="flex items-center gap-1.5 font-mono text-[10px] text-muted-foreground">
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: 'var(--destructive)', opacity: 0.6 }} />
                incorrect
              </span>
              <span className="flex items-center gap-1.5 font-mono text-[10px] text-muted-foreground">
                <span className="inline-block w-2.5 h-1 rounded-full" style={{ background: 'var(--chart-1)' }} />
                new words
              </span>
              {data && (
                <span className="ml-auto font-mono text-[10px] text-muted-foreground">
                  {data.total_reviews} reviews · {data.days_active}d active · {data.accuracy_percent.toFixed(0)}% accuracy
                </span>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
