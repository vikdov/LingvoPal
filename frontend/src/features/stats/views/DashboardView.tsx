import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PenLine, BookOpen, Compass, Flame, Sparkles, AlertTriangle, ArrowRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { useLanguageStore, useUserLanguages } from '@/features/languages';
import { AddFirstLanguagePrompt } from '@/features/languages';
import type { LanguageOverview, LanguageTotals } from '../types/stats.types';

function StatCard({ label, value, icon: Icon, sub, highlight }: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  sub?: string;
  highlight?: boolean;
}) {
  return (
    <Card className={highlight ? 'bg-primary/5 border-primary/30' : 'bg-card border-border'}>
      <CardContent className="pt-5 pb-4 flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className={`font-mono text-[10px] uppercase tracking-widest ${highlight ? 'text-primary/80' : 'text-muted-foreground'}`}>
            {label}
          </span>
          <Icon className={`size-3.5 ${highlight ? 'text-primary' : 'text-muted-foreground'}`} />
        </div>
        <span className={`text-2xl font-bold tracking-tight ${highlight ? 'text-primary' : 'text-foreground'}`}>{value}</span>
        {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
      </CardContent>
    </Card>
  );
}

function DueCard({ dueNow }: { dueNow: number }) {
  const { t } = useTranslation();
  const due = dueNow > 0;
  return (
    <Link
      to="/practice"
      className={`rounded-xl border transition-all ${due ? 'bg-primary/5 border-primary/30 hover:bg-primary/10' : 'bg-card border-border pointer-events-none'}`}
    >
      <div className="pt-5 pb-4 px-4 flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className={`font-mono text-[10px] uppercase tracking-widest ${due ? 'text-primary/80' : 'text-muted-foreground'}`}>
            {t('dashboard.wordsDue')}
          </span>
          <PenLine className={`size-3.5 ${due ? 'text-primary' : 'text-muted-foreground'}`} />
        </div>
        <span className={`text-2xl font-bold tracking-tight ${due ? 'text-primary' : 'text-foreground'}`}>{dueNow}</span>
        {due ? (
          <span className="text-[11px] text-primary/80 flex items-center gap-1 font-medium">
            {t('dashboard.startReview')} <ArrowRight className="size-3" />
          </span>
        ) : (
          <span className="text-[11px] text-muted-foreground">{t('dashboard.allCaughtUp')}</span>
        )}
      </div>
    </Link>
  );
}

function LearningBalanceBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3">
      <AlertTriangle className="size-4 text-amber-500 mt-0.5 shrink-0" />
      <p className="text-sm text-foreground leading-relaxed">{message}</p>
    </div>
  );
}

function EmptyState() {
  const { t } = useTranslation();
  const steps = [
    { step: '01', title: t('dashboard.step01Title'), body: t('dashboard.step01Body') },
    { step: '02', title: t('dashboard.step02Title'), body: t('dashboard.step02Body') },
    { step: '03', title: t('dashboard.step03Title'), body: t('dashboard.step03Body') },
  ];
  return (
    <div className="flex flex-col items-center justify-center gap-8 py-20 text-center">
      <div className="flex flex-col items-center gap-3">
        <div className="size-14 rounded-full bg-primary/10 flex items-center justify-center">
          <PenLine className="size-6 text-primary" />
        </div>
        <h2 className="text-xl font-semibold tracking-tight text-foreground">
          {t('dashboard.emptyTitle')}
        </h2>
        <p className="text-sm text-muted-foreground max-w-[36ch] leading-relaxed">
          {t('dashboard.emptyDescription')}
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <Button asChild>
          <Link to="/sets/discover">
            <Compass className="size-4" />
            {t('dashboard.findASet')}
          </Link>
        </Button>
        <Button variant="outline" asChild>
          <Link to="/sets">
            <BookOpen className="size-4" />
            {t('dashboard.createMyOwn')}
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-xl mt-4">
        {steps.map(({ step, title, body }) => (
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

export function DashboardView() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [selectedDays, setSelectedDays] = useState(30);
  const [scope, setScope] = useState('overall');

  const { data: userLangsData, isLoading: loadingUserLangs } = useUserLanguages();
  const { data: overview, isLoading: loadingOverview } = useOverview();
  const { data: totals, isLoading: loadingTotals } = useTotals();

  const hasLanguages = (userLangsData?.languages ?? []).length > 0;
  const languages: LanguageOverview[] = overview?.languages ?? [];
  const totalsList: LanguageTotals[] = totals ?? [];
  const hasData = languages.length > 0;

  const globalLangId = useLanguageStore((s) => s.activeLanguageId);
  const selectedLangId = globalLangId ?? languages[0]?.language_id ?? null;

  const { data: rangeStats, isLoading: loadingRange } = useRangeStats(selectedLangId, selectedDays);
  const { data: maturity, isLoading: loadingMaturity } = useVocabMaturity(selectedLangId);

  const activeLang = languages.find((l) => l.language_id === selectedLangId);
  const activeTotals = totalsList.find((t) => t.language_id === selectedLangId);

  const aggStreak    = Math.max(0, ...languages.map((l) => l.streak_days));
  const aggNewToday  = languages.reduce((s, l) => s + (l.today_new_words ?? 0), 0);
  const aggLearned   = totalsList.reduce((s, t) => s + (t.total_words_learned ?? 0), 0);
  const aggHours     = totalsList.reduce((s, t) => s + (t.total_hours ?? 0), 0);

  const displayStreak  = scope === 'overall' ? aggStreak  : (activeTotals?.streak_days ?? activeLang?.streak_days ?? 0);
  const displayNew     = scope === 'overall' ? aggNewToday : (activeLang?.today_new_words ?? 0);
  const displayLearned = scope === 'overall' ? aggLearned  : (activeTotals?.total_words_learned ?? 0);
  const displayHours   = scope === 'overall' ? aggHours    : (activeTotals?.total_hours ?? 0);

  function getGreeting() {
    const h = new Date().getHours();
    if (h < 12) return t('dashboard.greetingMorning');
    if (h < 17) return t('dashboard.greetingAfternoon');
    return t('dashboard.greetingEvening');
  }

  if (loadingOverview || loadingTotals || loadingUserLangs) return <LoadingSkeleton />;

  return (
    <div className="flex flex-col gap-6 p-6 lg:p-8 max-w-5xl mx-auto w-full">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            {getGreeting()}{user ? `, ${user.username}` : ''}.
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {hasLanguages && (
          <div className="flex items-center gap-2">
            <Select value={scope} onValueChange={setScope}>
              <SelectTrigger className="h-8 text-xs font-mono w-44 border-border">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="overall" className="text-xs font-mono">{t('dashboard.allLanguages')}</SelectItem>
                <SelectItem value="language" className="text-xs font-mono">
                  {activeLang ? t('dashboard.activeLanguageOnly', { name: activeLang.language_name ?? 'Language' }) : t('dashboard.activeLanguage')}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {!hasLanguages ? (
        <AddFirstLanguagePrompt />
      ) : !hasData ? (
        <EmptyState />
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label={t('dashboard.streak')}
              value={`${displayStreak}d`}
              icon={Flame}
              sub={scope === 'overall' ? t('dashboard.bestStreak') : t('dashboard.currentStreak')}
            />
            <StatCard
              label={t('dashboard.newToday')}
              value={displayNew}
              icon={Sparkles}
            />
            <StatCard
              label={t('dashboard.totalPracticed')}
              value={displayLearned}
              icon={BookOpen}
              sub={t('dashboard.totalHours', { hours: displayHours.toFixed(1) })}
            />
            <DueCard dueNow={overview?.total_due_now ?? 0} />
          </div>

          <DailyActivityChart
            data={rangeStats}
            selectedDays={selectedDays}
            onDaysChange={setSelectedDays}
            isLoading={loadingRange}
            langLabel={activeLang?.language_name ?? undefined}
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <MaturityDonut data={maturity} isLoading={loadingMaturity} langLabel={activeLang?.language_name ?? undefined} />
            <RecentlyStabilized data={maturity} isLoading={loadingMaturity} />
          </div>

          <StudyTimeTrend
            data={rangeStats?.daily}
            days={selectedDays}
            isLoading={loadingRange}
          />

          {maturity?.learning_balance && (
            <LearningBalanceBanner message={maturity.learning_balance.message} />
          )}
        </>
      )}
    </div>
  );
}
