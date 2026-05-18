import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { ApiError } from '@/services/api';
import { useMySettings, useUpdateSettings } from '../hooks/useSettings';
import type { UserSettingsPatch } from '../types/settings.types';
import { ThemeToggle } from './ThemeToggle';

export function PreferencesTab() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useMySettings();
  const updateSettings = useUpdateSettings();

  const PREFERENCES: {
    key: keyof UserSettingsPatch;
    label: string;
    description: string;
  }[] = [
    {
      key: 'show_translations',
      label: t('settings.preferences.showTranslations'),
      description: t('settings.preferences.showTranslationsHint'),
    },
    {
      key: 'show_images',
      label: t('settings.preferences.showImages'),
      description: t('settings.preferences.showImagesHint'),
    },
    {
      key: 'show_synonyms',
      label: t('settings.preferences.showSynonyms'),
      description: t('settings.preferences.showSynonymsHint'),
    },
    {
      key: 'show_part_of_speech',
      label: t('settings.preferences.showPartOfSpeech'),
      description: t('settings.preferences.showPartOfSpeechHint'),
    },
    {
      key: 'auto_play_audio',
      label: t('settings.preferences.autoPlayAudio'),
      description: t('settings.preferences.autoPlayAudioHint'),
    },
  ];

  function save(patch: UserSettingsPatch) {
    updateSettings.mutate(patch, {
      onError: (err) => toast.error(err instanceof ApiError ? err.message : t('common.failedSave')),
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
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t('settings.preferences.appearanceTitle')}</CardTitle>
          <CardDescription>{t('settings.preferences.appearanceDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between gap-4">
            <Label>{t('settings.preferences.themeLabel')}</Label>
            <ThemeToggle />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.preferences.displayTitle')}</CardTitle>
          <CardDescription>{t('settings.preferences.displayDescription')}</CardDescription>
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
    </div>
  );
}
