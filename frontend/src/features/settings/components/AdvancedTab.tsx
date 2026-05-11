import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { ApiError } from '@/services/api';
import { useMySettings, useUpdateSettings } from '../hooks/useSettings';
import type { RetentionPriority } from '../types/settings.types';

const RETENTION_OPTIONS: { value: RetentionPriority; label: string; description: string }[] = [
  { value: 'speed_learning', label: 'Speed', description: 'Learn fast, review less' },
  { value: 'balanced', label: 'Balanced', description: 'Default pace' },
  { value: 'long_term_mastery', label: 'Mastery', description: 'Deep retention' },
];

export function AdvancedTab() {
  const { data: settings, isLoading } = useMySettings();
  const updateSettings = useUpdateSettings();

  const [perDay, setPerDay] = useState('');
  const [perSession, setPerSession] = useState('');
  const [maxReview, setMaxReview] = useState('');
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (settings && !initialized) {
      setPerDay(String(settings.new_items_per_day_limit));
      setPerSession(String(settings.new_items_per_session));
      setMaxReview(settings.max_review_load_per_day != null ? String(settings.max_review_load_per_day) : '');
      setInitialized(true);
    }
  }, [settings, initialized]);

  function handleSaveLimits() {
    const parsedPerDay = parseInt(perDay, 10);
    const parsedPerSession = parseInt(perSession, 10);
    const parsedMaxReview = maxReview ? parseInt(maxReview, 10) : null;

    if (isNaN(parsedPerDay) || parsedPerDay < 1 || parsedPerDay > 500) {
      toast.error('New items per day must be between 1 and 500');
      return;
    }
    if (isNaN(parsedPerSession) || parsedPerSession < 1 || parsedPerSession > 100) {
      toast.error('New items per session must be between 1 and 100');
      return;
    }
    if (parsedMaxReview !== null && (isNaN(parsedMaxReview) || parsedMaxReview < 1 || parsedMaxReview > 9999)) {
      toast.error('Max review load must be between 1 and 9999, or empty for unlimited');
      return;
    }

    updateSettings.mutate(
      {
        new_items_per_day_limit: parsedPerDay,
        new_items_per_session: parsedPerSession,
        max_review_load_per_day: parsedMaxReview,
      },
      {
        onSuccess: () => toast.success('Limits saved'),
        onError: (err) => toast.error(err instanceof ApiError ? err.message : 'Failed to save'),
      },
    );
  }

  function handleRetentionChange(v: string) {
    if (!v) return;
    updateSettings.mutate(
      { retention_priority: v as RetentionPriority },
      {
        onError: (err) => toast.error(err instanceof ApiError ? err.message : 'Failed to save'),
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
      {/* Item limits */}
      <Card>
        <CardHeader>
          <CardTitle>Item limits</CardTitle>
          <CardDescription>Control how many new items enter your queue each day and session.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="per-day">New items per day</Label>
              <Input
                id="per-day"
                type="number"
                min={1}
                max={500}
                value={perDay}
                onChange={(e) => setPerDay(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Max 500.</p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="per-session">New items per session</Label>
              <Input
                id="per-session"
                type="number"
                min={1}
                max={100}
                value={perSession}
                onChange={(e) => setPerSession(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Max 100.</p>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="max-review">Max reviews per day</Label>
            <Input
              id="max-review"
              type="number"
              min={1}
              max={9999}
              value={maxReview}
              onChange={(e) => setMaxReview(e.target.value)}
              placeholder="Unlimited"
            />
            <p className="text-xs text-muted-foreground">Leave empty for no cap on daily reviews.</p>
          </div>
          <Button onClick={handleSaveLimits} disabled={updateSettings.isPending}>
            Save limits
          </Button>
        </CardContent>
      </Card>

      {/* Retention priority */}
      <Card>
        <CardHeader>
          <CardTitle>Retention priority</CardTitle>
          <CardDescription>
            Tune the trade-off between learning speed and long-term retention.
          </CardDescription>
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
    </div>
  );
}
