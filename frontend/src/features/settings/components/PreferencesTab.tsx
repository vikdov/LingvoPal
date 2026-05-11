import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { ApiError } from '@/services/api';
import { useMySettings, useUpdateSettings } from '../hooks/useSettings';
import type { UserSettingsPatch } from '../types/settings.types';

const PREFERENCES: {
  key: keyof UserSettingsPatch;
  label: string;
  description: string;
}[] = [
  {
    key: 'show_translations',
    label: 'Show translations',
    description: 'Display a translation hint alongside each item during practice.',
  },
  {
    key: 'show_images',
    label: 'Show images',
    description: 'Show contextual images when available.',
  },
  {
    key: 'show_synonyms',
    label: 'Show synonyms',
    description: 'Display synonym hints on the card.',
  },
  {
    key: 'show_part_of_speech',
    label: 'Show part of speech',
    description: 'Label items with their grammatical role (noun, verb, etc.).',
  },
  {
    key: 'auto_play_audio',
    label: 'Auto-play audio',
    description: 'Automatically play pronunciation audio when a card is shown.',
  },
];

export function PreferencesTab() {
  const { data: settings, isLoading } = useMySettings();
  const updateSettings = useUpdateSettings();

  function save(patch: UserSettingsPatch) {
    updateSettings.mutate(patch, {
      onError: (err) => toast.error(err instanceof ApiError ? err.message : 'Failed to save settings'),
    });
  }

  if (isLoading || !settings) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-56" />
        </CardHeader>
        <CardContent className="space-y-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="space-y-1">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
              <Skeleton className="h-5 w-8 rounded-full" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Display preferences</CardTitle>
        <CardDescription>Control what extra information is shown during practice.</CardDescription>
      </CardHeader>
      <CardContent className="divide-y">
        {PREFERENCES.map(({ key, label, description }) => (
          <div key={key} className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0">
            <div className="space-y-0.5">
              <Label>{label}</Label>
              <p className="text-xs text-muted-foreground">{description}</p>
            </div>
            <Switch
              checked={Boolean(settings[key as keyof typeof settings])}
              onCheckedChange={(v) => save({ [key]: v })}
              disabled={updateSettings.isPending}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
