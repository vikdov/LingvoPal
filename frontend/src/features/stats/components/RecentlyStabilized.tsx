import { Trophy, Star, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { VocabMaturity } from '../types/stats.types';

interface Props {
  data: VocabMaturity | undefined;
  isLoading: boolean;
}

interface MilestoneRowProps {
  icon: React.ComponentType<{ className?: string }>;
  iconClass: string;
  count: number;
  label: string;
}

function MilestoneRow({ icon: Icon, iconClass, count, label }: MilestoneRowProps) {
  if (count === 0) return null;
  return (
    <div className="flex items-center gap-3 py-2">
      <div className={`size-7 rounded-full flex items-center justify-center shrink-0 ${iconClass}`}>
        <Icon className="size-3.5" />
      </div>
      <div>
        <p className="text-sm font-semibold text-foreground">
          {count} word{count !== 1 ? 's' : ''} {label}
        </p>
        <p className="font-mono text-[10px] text-muted-foreground">this week</p>
      </div>
    </div>
  );
}

export function RecentlyStabilized({ data, isLoading }: Props) {
  const hasActivity = data && (data.recently_mature > 0 || data.recently_long_term > 0 || data.new_this_month > 0);

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
        ) : !hasActivity ? (
          <div className="py-4 text-center">
            <p className="text-sm text-muted-foreground">Keep reviewing — milestones coming soon.</p>
            <p className="font-mono text-[10px] text-muted-foreground mt-1">
              Words become Mature after 22+ day intervals.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            <MilestoneRow
              icon={Trophy}
              iconClass="bg-primary/10 text-primary"
              count={data.recently_mature}
              label="became Mature"
            />
            <MilestoneRow
              icon={Star}
              iconClass="bg-amber-500/10 text-amber-500"
              count={data.recently_long_term}
              label="entered Long-term memory"
            />
          </div>
        )}

        {data && data.new_this_month > 0 && (
          <div className="mt-3 pt-3 border-t border-border flex items-center gap-2">
            <TrendingUp className="size-3.5 text-primary shrink-0" />
            <p className="text-sm text-foreground">
              <span className="font-bold">+{data.new_this_month}</span>{' '}
              <span className="text-muted-foreground font-mono text-xs">new words this month</span>
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
