import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { ApiError } from '@/services/api';
import { useMySettings, useUpdateSettings } from '../hooks/useSettings';
import type { RetentionPriority } from '../types/settings.types';

export function AdvancedTab() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useMySettings();
  const updateSettings = useUpdateSettings();

  const RETENTION_OPTIONS: { value: RetentionPriority; label: string; description: string }[] = [
    { value: 'speed_learning', label: t('settings.advanced.retentionSpeed'), description: t('settings.advanced.retentionSpeedHint') },
    { value: 'balanced', label: t('settings.advanced.retentionBalanced'), description: t('settings.advanced.retentionBalancedHint') },
    { value: 'long_term_mastery', label: t('settings.advanced.retentionMastery'), description: t('settings.advanced.retentionMasteryHint') },
  ];

  const [perDay, setPerDay] = useState('');
  const [perSession, setPerSession] = useState('');
  const [maxReview, setMaxReview] = useState('');
  const [reminderTime, setReminderTime] = useState('');
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (settings && !initialized) {
      setPerDay(String(settings.new_items_per_day_limit));
      setPerSession(String(settings.new_items_per_session));
      setMaxReview(settings.max_review_load_per_day != null ? String(settings.max_review_load_per_day) : '');
      setReminderTime(settings.reminder_time ?? '');
      setInitialized(true);
    }
  }, [settings, initialized]);

  function handleSaveLimits() {
    const parsedPerDay = parseInt(perDay, 10);
    const parsedPerSession = parseInt(perSession, 10);
    const parsedMaxReview = maxReview ? parseInt(maxReview, 10) : null;

    if (isNaN(parsedPerDay) || parsedPerDay < 1 || parsedPerDay > 500) {
      toast.error(t('settings.advanced.perDayError'));
      return;
    }
    if (isNaN(parsedPerSession) || parsedPerSession < 1 || parsedPerSession > 100) {
      toast.error(t('settings.advanced.perSessionError'));
      return;
    }
    if (parsedMaxReview !== null && (isNaN(parsedMaxReview) || parsedMaxReview < 1 || parsedMaxReview > 9999)) {
      toast.error(t('settings.advanced.maxReviewError'));
      return;
    }

    updateSettings.mutate(
      {
        new_items_per_day_limit: parsedPerDay,
        new_items_per_session: parsedPerSession,
        max_review_load_per_day: parsedMaxReview,
      },
      {
        onSuccess: () => toast.success(t('settings.advanced.limitsSaved')),
        onError: (err) => toast.error(err instanceof ApiError ? err.message : t('common.failedSave_short')),
      },
    );
  }

  function handleRetentionChange(v: string) {
    if (!v) return;
    updateSettings.mutate(
      { retention_priority: v as RetentionPriority },
      {
        onError: (err) => toast.error(err instanceof ApiError ? err.message : t('common.failedSave_short')),
      },
    );
  }

  function handleStreakToggle(enabled: boolean) {
    updateSettings.mutate(
      { streak_reminders_enabled: enabled },
      {
        onError: (err) => toast.error(err instanceof ApiError ? err.message : t('common.failedSave_short')),
      },
    );
  }

  function handleSaveReminderTime() {
    updateSettings.mutate(
      { reminder_time: reminderTime || null },
      {
        onSuccess: () => toast.success(t('settings.advanced.reminderSaved')),
        onError: (err) => toast.error(err instanceof ApiError ? err.message : t('common.failedSave_short')),
      },
    );
  }

  if (isLoading || !settings) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader><Skeleton className="h-5 w-40" /></CardHeader>
          <CardContent className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="space-y-1.5">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-9 w-full" />
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><Skeleton className="h-5 w-36" /></CardHeader>
          <CardContent><Skeleton className="h-10 w-full" /></CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t('settings.advanced.limitsTitle')}</CardTitle>
          <CardDescription>{t('settings.advanced.limitsDescription')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="per-day">{t('settings.advanced.perDayLabel')}</Label>
              <Input
                id="per-day"
                type="number"
                min={1}
                max={500}
                value={perDay}
                onChange={(e) => setPerDay(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">{t('settings.advanced.perDayHint')}</p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="per-session">{t('settings.advanced.perSessionLabel')}</Label>
              <Input
                id="per-session"
                type="number"
                min={1}
                max={100}
                value={perSession}
                onChange={(e) => setPerSession(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">{t('settings.advanced.perSessionHint')}</p>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="max-review">{t('settings.advanced.maxReviewLabel')}</Label>
            <Input
              id="max-review"
              type="number"
              min={1}
              max={9999}
              value={maxReview}
              onChange={(e) => setMaxReview(e.target.value)}
              placeholder={t('settings.advanced.maxReviewPlaceholder')}
            />
            <p className="text-xs text-muted-foreground">{t('settings.advanced.maxReviewHint')}</p>
          </div>
          <Button onClick={handleSaveLimits} disabled={updateSettings.isPending}>
            {t('settings.advanced.saveLimits')}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.advanced.retentionTitle')}</CardTitle>
          <CardDescription>{t('settings.advanced.retentionDescription')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ToggleGroup
            type="single"
            variant="outline"
            value={settings.retention_priority}
            onValueChange={handleRetentionChange}
            className="w-full"
          >
            {RETENTION_OPTIONS.map((o) => (
              <ToggleGroupItem key={o.value} value={o.value} className="flex-1 flex-col gap-0.5 h-auto py-3">
                <span className="font-medium">{o.label}</span>
                <span className="text-[10px] text-muted-foreground font-normal">{o.description}</span>
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.advanced.notificationsTitle')}</CardTitle>
          <CardDescription>{t('settings.advanced.notificationsDescription')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="space-y-0.5">
              <Label htmlFor="streak-reminders">{t('settings.advanced.streakReminders')}</Label>
              <p className="text-xs text-muted-foreground">{t('settings.advanced.streakRemindersHint')}</p>
            </div>
            <Switch
              id="streak-reminders"
              checked={settings.streak_reminders_enabled}
              onCheckedChange={handleStreakToggle}
              disabled={updateSettings.isPending}
            />
          </div>
          {settings.streak_reminders_enabled && (
            <div className="space-y-2 pt-1">
              <Label htmlFor="reminder-time">{t('settings.advanced.reminderTimeLabel')}</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="reminder-time"
                  type="time"
                  value={reminderTime}
                  onChange={(e) => setReminderTime(e.target.value)}
                  className="w-36"
                />
                <Button size="sm" onClick={handleSaveReminderTime} disabled={updateSettings.isPending}>
                  {t('settings.advanced.save')}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">{t('settings.advanced.reminderTimeHint')}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
