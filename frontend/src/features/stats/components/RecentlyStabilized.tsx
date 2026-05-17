import { Trophy, Star, Lock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { VocabMaturity } from '../types/stats.types';

interface Props {
  data: VocabMaturity | undefined;
  isLoading: boolean;
}

export function RecentlyStabilized({ data, isLoading }: Props) {
  const matureCount  = data?.buckets.find((b) => b.key === 'mature')?.count ?? 0;
  const longTermCount = data?.buckets.find((b) => b.key === 'long_term')?.count ?? 0;

  const milestones = [
    {
      label: 'First word retained',
      hint: 'review a word for 22+ days',
      icon: Trophy,
      achieved: matureCount >= 1,
      recent: data?.recently_mature ?? 0,
      iconAchieved: 'bg-primary/10 text-primary',
    },
    {
      label: '5 words retained',
      hint: 'build consistency',
      icon: Trophy,
      achieved: matureCount >= 5,
      recent: 0,
      iconAchieved: 'bg-primary/10 text-primary',
    },
    {
      label: 'First long-term word',
      hint: '4+ month review interval',
      icon: Star,
      achieved: longTermCount >= 1,
      recent: data?.recently_long_term ?? 0,
      iconAchieved: 'bg-amber-500/10 text-amber-500',
    },
    {
      label: '10 long-term words',
      hint: 'deep vocabulary foundation',
      icon: Star,
      achieved: longTermCount >= 10,
      recent: 0,
      iconAchieved: 'bg-amber-500/10 text-amber-500',
    },
  ];

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-foreground">Progress Milestones</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-10 w-full rounded-md" />
            <Skeleton className="h-10 w-3/4 rounded-md" />
          </div>
        ) : (
          <div className="flex flex-col divide-y divide-border">
            {milestones.map((m) => {
              const Icon = m.achieved ? m.icon : Lock;
              return (
                <div key={m.label} className={`flex items-center gap-3 py-2.5 ${m.achieved ? '' : 'opacity-40'}`}>
                  <div className={`size-7 rounded-full flex items-center justify-center shrink-0 ${m.achieved ? m.iconAchieved : 'bg-muted'}`}>
                    <Icon className="size-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-foreground leading-none">{m.label}</p>
                    <p className="font-mono text-xs text-muted-foreground mt-0.5">{m.hint}</p>
                  </div>
                  {m.achieved && m.recent > 0 && (
                    <span className="text-[10px] font-mono text-primary shrink-0">+{m.recent} this week</span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
