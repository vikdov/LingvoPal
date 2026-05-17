import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { DailyStats } from '../types/stats.types';

interface Props {
  data: DailyStats[] | undefined;
  days: number;
  isLoading: boolean;
}

function buildTimeSeries(data: DailyStats[] | undefined, days: number) {
  const map = new Map<string, number>();
  if (data) {
    for (const d of data) {
      map.set(d.stat_date, (map.get(d.stat_date) ?? 0) + d.seconds_spent / 60);
    }
  }
  const series: { label: string; minutes: number }[] = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const iso = d.toISOString().slice(0, 10);
    const label = d.toLocaleDateString('en-US', days <= 7 ? { weekday: 'short' } : { month: 'short', day: 'numeric' });
    series.push({ label, minutes: Math.round((map.get(iso) ?? 0) * 10) / 10 });
  }
  return series;
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload?.length || payload[0].value === 0) return null;
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 shadow-md font-mono text-xs">
      <p className="text-muted-foreground">{label}</p>
      <p className="text-foreground">{payload[0].value} min</p>
    </div>
  );
}

export function StudyTimeTrend({ data, days, isLoading }: Props) {
  const series = buildTimeSeries(data, days);
  const totalMinutes = series.reduce((s, r) => s + r.minutes, 0);

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold text-foreground">Study Time</CardTitle>
          {totalMinutes > 0 && (
            <span className="font-mono text-[10px] text-muted-foreground">
              {totalMinutes >= 60
                ? `${(totalMinutes / 60).toFixed(1)}h total`
                : `${Math.round(totalMinutes)}min total`}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-24 w-full rounded-md" />
        ) : (
          <ResponsiveContainer width="100%" height={96}>
            <AreaChart data={series} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
              <defs>
                <linearGradient id="studyTimeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--chart-3)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--chart-3)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke="var(--border)" strokeOpacity={0.5} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fontFamily: 'var(--font-mono)', fill: 'var(--color-muted-foreground)' }}
                tickLine={false}
                axisLine={false}
                interval={days <= 7 ? 0 : days <= 30 ? 6 : 13}
              />
              <YAxis
                tick={{ fontSize: 11, fontFamily: 'var(--font-mono)', fill: 'var(--color-muted-foreground)' }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
                unit="m"
                width={32}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--border)' }} />
              <Area
                type="monotone"
                dataKey="minutes"
                stroke="var(--chart-3)"
                strokeWidth={1.5}
                fill="url(#studyTimeGrad)"
                dot={false}
                activeDot={{ r: 3, fill: 'var(--chart-3)' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
