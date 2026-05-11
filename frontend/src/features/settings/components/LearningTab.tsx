import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { ApiError } from '@/services/api';
import { useAllLanguages } from '@/features/languages';
import { useMySettings, useUpdateSettings } from '../hooks/useSettings';
import type { LearningIntensity, EvaluationMode } from '../types/settings.types';

const INTENSITY_OPTIONS: { value: LearningIntensity; label: string }[] = [
  { value: 'light', label: 'Light' },
  { value: 'balanced', label: 'Balanced' },
  { value: 'intensive', label: 'Intensive' },
];

const EVAL_OPTIONS: { value: EvaluationMode; label: string }[] = [
  { value: 'forgiving', label: 'Forgiving' },
  { value: 'normal', label: 'Normal' },
  { value: 'strict', label: 'Strict' },
];

function SettingsSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="space-y-1.5">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-9 w-full" />
        </div>
      ))}
    </div>
  );
}

function SwitchRow({
  label,
  description,
  checked,
  onCheckedChange,
  disabled,
}: {
  label: string;
  description?: string;
  checked: boolean;
  onCheckedChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="space-y-0.5">
        <Label>{label}</Label>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} disabled={disabled} />
    </div>
  );
}

export function LearningTab() {
  const { data: settings, isLoading } = useMySettings();
  const { data: languages } = useAllLanguages();
  const updateSettings = useUpdateSettings();

  const [dailyGoal, setDailyGoal] = useState('');
  const [goalInitialized, setGoalInitialized] = useState(false);
  const [reminderTime, setReminderTime] = useState('');
  const [reminderInitialized, setReminderInitialized] = useState(false);

  useEffect(() => {
    if (settings && !goalInitialized) {
      setDailyGoal(String(settings.daily_study_goal));
      setGoalInitialized(true);
    }
    if (settings && !reminderInitialized) {
      setReminderTime(settings.reminder_time ? settings.reminder_time.slice(0, 5) : '');
      setReminderInitialized(true);
    }
  }, [settings, goalInitialized, reminderInitialized]);

  function save(patch: Parameters<typeof updateSettings.mutate>[0], silent = false) {
    updateSettings.mutate(patch, {
      onError: (err) => toast.error(err instanceof ApiError ? err.message : 'Failed to save settings'),
      onSuccess: silent ? undefined : () => toast.success('Settings saved'),
    });
  }

  function handleSaveSchedule() {
    const parsed = parseInt(dailyGoal, 10);
    if (isNaN(parsed) || parsed < 1 || parsed > 9999) {
      toast.error('Daily goal must be between 1 and 9999');
      return;
    }
    save({
      daily_study_goal: parsed,
      reminder_time: reminderTime || null,
    });
  }

  if (isLoading || !settings) {
    return (
      <div className="space-y-6">
        <Card><CardHeader><Skeleton className="h-5 w-32" /></CardHeader><CardContent><SettingsSkeleton /></CardContent></Card>
        <Card><CardHeader><Skeleton className="h-5 w-40" /></CardHeader><CardContent><SettingsSkeleton /></CardContent></Card>
        <Card><CardHeader><Skeleton className="h-5 w-24" /></CardHeader><CardContent><SettingsSkeleton /></CardContent></Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Languages */}
      <Card>
        <CardHeader>
          <CardTitle>Languages</CardTitle>
          <CardDescription>Your native and interface language preferences.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label>Native language</Label>
            <Select
              value={String(settings.native_language.id)}
              onValueChange={(v) => save({ native_lang_id: Number(v) }, true)}
              disabled={updateSettings.isPending}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {languages?.map((l) => (
                  <SelectItem key={l.id} value={String(l.id)}>
                    {l.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Interface language</Label>
            <Select
              value={String(settings.interface_language.id)}
              onValueChange={(v) => save({ interface_lang_id: Number(v) }, true)}
              disabled={updateSettings.isPending}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {languages?.map((l) => (
                  <SelectItem key={l.id} value={String(l.id)}>
                    {l.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Learning behavior */}
      <Card>
        <CardHeader>
          <CardTitle>Learning behavior</CardTitle>
          <CardDescription>How practice sessions are structured and graded.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>Learning intensity</Label>
            <ToggleGroup
              type="single"
              variant="outline"
              value={settings.learning_intensity}
              onValueChange={(v) => v && save({ learning_intensity: v as LearningIntensity }, true)}
              className="w-full"
            >
              {INTENSITY_OPTIONS.map((o) => (
                <ToggleGroupItem key={o.value} value={o.value} className="flex-1">
                  {o.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
            <p className="text-xs text-muted-foreground">
              Controls how aggressively SM-2 intervals are scaled.
            </p>
          </div>

          <div className="space-y-2">
            <Label>Evaluation strictness</Label>
            <ToggleGroup
              type="single"
              variant="outline"
              value={settings.evaluation_mode}
              onValueChange={(v) => v && save({ evaluation_mode: v as EvaluationMode }, true)}
              className="w-full"
            >
              {EVAL_OPTIONS.map((o) => (
                <ToggleGroupItem key={o.value} value={o.value} className="flex-1">
                  {o.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
            <p className="text-xs text-muted-foreground">
              How strictly typed answers are graded (typos, capitalisation, etc.).
            </p>
          </div>

          <SwitchRow
            label="Show hints on failure"
            description="Display the correct answer after a wrong attempt."
            checked={settings.show_hints_on_fails}
            onCheckedChange={(v) => save({ show_hints_on_fails: v }, true)}
            disabled={updateSettings.isPending}
          />
        </CardContent>
      </Card>

      {/* Schedule */}
      <Card>
        <CardHeader>
          <CardTitle>Schedule</CardTitle>
          <CardDescription>Daily goals and reminder settings.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="daily-goal">Daily study goal (items)</Label>
              <Input
                id="daily-goal"
                type="number"
                min={1}
                max={9999}
                value={dailyGoal}
                onChange={(e) => setDailyGoal(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="reminder-time">Reminder time</Label>
              <Input
                id="reminder-time"
                type="time"
                value={reminderTime}
                onChange={(e) => setReminderTime(e.target.value)}
              />
            </div>
          </div>
          <SwitchRow
            label="Streak reminders"
            description="Get notified if you're about to break your streak."
            checked={settings.streak_reminders_enabled}
            onCheckedChange={(v) => save({ streak_reminders_enabled: v }, true)}
            disabled={updateSettings.isPending}
          />
          <Button onClick={handleSaveSchedule} disabled={updateSettings.isPending}>
            Save schedule
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
