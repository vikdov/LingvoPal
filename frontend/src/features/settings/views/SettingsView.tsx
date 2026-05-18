import { useTranslation } from 'react-i18next';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AccountTab } from '../components/AccountTab';
import { LearningTab } from '../components/LearningTab';
import { PreferencesTab } from '../components/PreferencesTab';
import { AdvancedTab } from '../components/AdvancedTab';
import { DangerZoneTab } from '../components/DangerZoneTab';
import { SubmissionsTab } from '../components/SubmissionsTab';

export function SettingsView() {
  const { t } = useTranslation();

  const TABS = [
    { value: 'account', label: t('settings.tabs.account') },
    { value: 'learning', label: t('settings.tabs.learning') },
    { value: 'preferences', label: t('settings.tabs.preferences') },
    { value: 'submissions', label: t('settings.tabs.submissions') },
    { value: 'advanced', label: t('settings.tabs.advanced') },
    { value: 'danger', label: t('settings.tabs.dangerZone') },
  ] as const;

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t('settings.title')}</h1>
        <p className="text-sm text-muted-foreground">{t('settings.subtitle')}</p>
      </div>

      <Tabs defaultValue="account">
        <TabsList className="mb-6 flex h-auto flex-wrap gap-1 bg-transparent p-0">
          {TABS.map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              className="rounded-md border border-transparent px-3 py-1.5 text-sm data-[state=active]:border-border data-[state=active]:bg-background data-[state=active]:shadow-sm"
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="account">
          <AccountTab />
        </TabsContent>
        <TabsContent value="learning">
          <LearningTab />
        </TabsContent>
        <TabsContent value="preferences">
          <PreferencesTab />
        </TabsContent>
        <TabsContent value="submissions">
          <SubmissionsTab />
        </TabsContent>
        <TabsContent value="advanced">
          <AdvancedTab />
        </TabsContent>
        <TabsContent value="danger">
          <DangerZoneTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
