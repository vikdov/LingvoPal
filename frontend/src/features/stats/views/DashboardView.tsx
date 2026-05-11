import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PenLine, BookOpen, Compass, Flame, CheckCircle2, Sparkles, AlertTriangle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { useOverview, useTotals, useRangeStats, useVocabMaturity } from '../hooks/useStats';
import { DailyActivityChart } from '../components/DailyActivityChart';
import { MaturityDonut } from '../components/MaturityDonut';
import { RecentlyStabilized } from '../components/RecentlyStabilized';
import { StudyTimeTrend } from '../components/StudyTimeTrend';
import { useLanguageStore } from '@/features/languages';
import type { LanguageOverview, LanguageTotals } from '../types/stats.types';

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function formatDate() {
  return new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
}

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, icon: Icon, sub }: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  sub?: string;
}) {
  return (
    <Card className="bg-card border-border">
      <CardContent className="pt-5 pb-4 flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {label}
          </span>
          <Icon className="size-3.5 text-muted-foreground" />
        </div>
        <span className="text-2xl font-bold tracking-tight text-foreground">{value}</span>
        {sub && <span className="text-[11px] text-muted-foreground">{sub}</span>}
      </CardContent>
    </Card>
  );
}

// ── Learning balance banner ───────────────────────────────────────────────────

function LearningBalanceBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3">
      <AlertTriangle className="size-4 text-amber-500 mt-0.5 shrink-0" />
      <p className="text-sm text-foreground leading-relaxed">{message}</p>
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-8 py-20 text-center">
      <div className="flex flex-col items-center gap-3">
        <div className="size-14 rounded-full bg-primary/10 flex items-center justify-center">
          <PenLine className="size-6 text-primary" />
        </div>
        <h2 className="text-xl font-semibold tracking-tight text-foreground">
          Your practice journey starts here.
        </h2>
        <p className="text-sm text-muted-foreground max-w-[36ch] leading-relaxed">
          Add words to a set, then practice them. After your first session, this page fills with your progress.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <Button asChild>
          <Link to="/sets">
            <BookOpen className="size-4" />
            Browse my sets
          </Link>
        </Button>
        <Button variant="outline" asChild>
          <Link to="/sets/discover">
            <Compass className="size-4" />
            Discover sets
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-xl mt-4">
        {[
          { step: '01', title: 'Add a set', body: 'Create your own or clone from the community.' },
          { step: '02', title: 'Practice daily', body: 'Type the word from memory in its sentence.' },
          { step: '03', title: 'Track retention', body: 'SM-2 schedules reviews. Your stats grow here.' },
        ].map(({ step, title, body }) => (
          <div key={step} className="flex flex-col gap-2 p-4 rounded-lg border border-border bg-card text-left">
            <span className="font-mono text-[10px] text-primary uppercase tracking-widest">{step}</span>
            <p className="text-sm font-semibold text-foreground">{title}</p>
            <p className="text-xs text-muted-foreground leading-relaxed">{body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Loading skeleton ──────────────────────────────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-6 p-6 lg:p-8 max-w-5xl mx-auto">
      <div className="flex flex-col gap-1">
        <Skeleton className="h-7 w-56" />
        <Skeleton className="h-4 w-32 mt-1" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-56 rounded-xl" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Skeleton className="h-52 rounded-xl" />
        <Skeleton className="h-52 rounded-xl" />
      </div>
      <Skeleton className="h-32 rounded-xl" />
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export function DashboardView() {
  const { user } = useAuth();
  const [selectedDays, setSelectedDays] = useState(30);
  const [scope, setScope] = useState('overall');

  const { data: overview, isLoading: loadingOverview } = useOverview();
  const { data: totals, isLoading: loadingTotals } = useTotals();

  const languages: LanguageOverview[] = overview?.languages ?? [];
  const totalsList: LanguageTotals[] = totals ?? [];
  const hasData = languages.length > 0;

  const globalLangId = useLanguageStore((s) => s.activeLanguageId);
  const selectedLangId = globalLangId ?? languages[0]?.language_id ?? null;

  const { data: rangeStats, isLoading: loadingRange } = useRangeStats(selectedLangId, selectedDays);
  const { data: maturity, isLoading: loadingMaturity } = useVocabMaturity(selectedLangId);

  const activeLang = languages.find((l) => l.language_id === selectedLangId);
  const activeTotals = totalsList.find((t) => t.language_id === selectedLangId);

  if (loadingOverview || loadingTotals) return <LoadingSkeleton />;

  return (
    <div className="flex flex-col gap-6 p-6 lg:p-8 max-w-5xl mx-auto w-full">

      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            {getGreeting()}{user ? `, ${user.username}` : ''}.
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">{formatDate()}</p>
        </div>

        <div className="flex items-center gap-2">
          <Select value={scope} onValueChange={setScope}>
            <SelectTrigger className="h-8 text-xs font-mono w-36 border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="overall" className="text-xs font-mono">Overall</SelectItem>
              <SelectItem value="sets" className="text-xs font-mono">All user sets</SelectItem>
            </SelectContent>
          </Select>

          {hasData && overview && overview.total_due_now > 0 && (
            <Button asChild size="sm" style={{ boxShadow: '0 0 20px -6px oklch(from var(--primary) l c h / 0.5)' }}>
              <Link to="/practice">
                <PenLine className="size-4" />
                {overview.total_due_now} due now
              </Link>
            </Button>
          )}
          {hasData && overview?.total_due_now === 0 && (
            <Badge variant="outline" className="gap-1.5 text-xs font-mono">
              <CheckCircle2 className="size-3 text-primary" /> All caught up
            </Badge>
          )}
        </div>
      </div>

      {!hasData ? (
        <EmptyState />
      ) : (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Streak"
              value={`${activeTotals?.streak_days ?? activeLang?.streak_days ?? 0}d`}
              icon={Flame}
              sub="current streak"
            />
            <StatCard
              label="New today"
              value={activeLang?.today_new_words ?? 0}
              icon={Sparkles}
              sub={`${activeLang?.today_correct ?? 0} correct today`}
            />
            <StatCard
              label="Total practiced"
              value={activeTotals?.total_words_learned ?? 0}
              icon={BookOpen}
              sub={`${(activeTotals?.total_hours ?? 0).toFixed(1)}h total`}
            />
            <StatCard
              label="Words due"
              value={overview?.total_due_now ?? 0}
              icon={PenLine}
              sub="ready for review"
            />
          </div>

          {/* Daily activity chart */}
          <DailyActivityChart
            data={rangeStats}
            selectedDays={selectedDays}
            onDaysChange={setSelectedDays}
            isLoading={loadingRange}
          />

          {/* Maturity + milestones */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <MaturityDonut data={maturity} isLoading={loadingMaturity} />
            <RecentlyStabilized data={maturity} isLoading={loadingMaturity} />
          </div>

          {/* Study time trend (soft metric) */}
          <StudyTimeTrend
            data={rangeStats?.daily}
            days={selectedDays}
            isLoading={loadingRange}
          />

          {/* Learning balance warning */}
          {maturity?.learning_balance && (
            <LearningBalanceBanner message={maturity.learning_balance.message} />
          )}

          {/* Quick actions */}
          <div className="flex gap-3 flex-wrap">
            <Button asChild variant="outline" size="sm">
              <Link to="/practice">
                <PenLine className="size-3.5" /> Practice now
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link to="/sets">
                <BookOpen className="size-3.5" /> My sets
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link to="/sets/discover">
                <Compass className="size-3.5" /> Discover
              </Link>
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
