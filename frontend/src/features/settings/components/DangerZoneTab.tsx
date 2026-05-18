import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { RotateCcw, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ApiError } from '@/services/api';
import { useAuthStore } from '@/features/auth/store/auth.store';
import { useResetSettings, useDeleteAccount, useMyProfile } from '../hooks/useSettings';

export function DangerZoneTab() {
  const { t } = useTranslation();
  const { data: profile } = useMyProfile();
  const resetSettings = useResetSettings();
  const deleteAccount = useDeleteAccount();
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const navigate = useNavigate();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [confirmEmail, setConfirmEmail] = useState('');
  const [resetConfirmOpen, setResetConfirmOpen] = useState(false);

  function handleReset() {
    resetSettings.mutate(undefined, {
      onSuccess: () => {
        setResetConfirmOpen(false);
        toast.success(t('settings.danger.resetSuccess'));
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : t('settings.danger.failedReset')),
    });
  }

  function handleDelete() {
    deleteAccount.mutate(undefined, {
      onSuccess: () => {
        clearAuth();
        navigate('/', { replace: true });
        toast.success(t('settings.danger.deleteSuccess'));
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : t('settings.danger.failedDelete')),
    });
  }

  const deleteConfirmed = confirmEmail === profile?.email;

  return (
    <div className="space-y-6">
      <Card className="border-amber-200 dark:border-amber-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RotateCcw className="size-4" />
            {t('settings.danger.resetTitle')}
          </CardTitle>
          <CardDescription>{t('settings.danger.resetDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={resetConfirmOpen} onOpenChange={setResetConfirmOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="border-amber-300 text-amber-700 hover:bg-amber-50 dark:border-amber-700 dark:text-amber-400 dark:hover:bg-amber-950/30">
                {t('settings.danger.resetToDefaults')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('settings.danger.resetDialogTitle')}</DialogTitle>
                <DialogDescription>{t('settings.danger.resetDialogDescription')}</DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setResetConfirmOpen(false)}>
                  {t('common.cancel')}
                </Button>
                <Button
                  variant="outline"
                  className="border-amber-300 text-amber-700 hover:bg-amber-50 dark:border-amber-700 dark:text-amber-400"
                  onClick={handleReset}
                  disabled={resetSettings.isPending}
                >
                  {resetSettings.isPending ? t('settings.danger.resetting') : t('settings.danger.yesReset')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>

      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <Trash2 className="size-4" />
            {t('settings.danger.deleteTitle')}
          </CardTitle>
          <CardDescription>{t('settings.danger.deleteDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={deleteDialogOpen} onOpenChange={(open) => { setDeleteDialogOpen(open); if (!open) setConfirmEmail(''); }}>
            <DialogTrigger asChild>
              <Button variant="destructive">{t('settings.danger.deleteMyAccount')}</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('settings.danger.deleteDialogTitle')}</DialogTitle>
                <DialogDescription>{t('settings.danger.deleteDialogDescription')}</DialogDescription>
              </DialogHeader>
              <div className="space-y-1.5 py-2">
                <Label htmlFor="confirm-email">
                  {t('settings.danger.confirmEmailLabel', { email: profile?.email })}
                </Label>
                <Input
                  id="confirm-email"
                  type="email"
                  value={confirmEmail}
                  onChange={(e) => setConfirmEmail(e.target.value)}
                  placeholder={profile?.email}
                  autoComplete="off"
                />
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => { setDeleteDialogOpen(false); setConfirmEmail(''); }}>
                  {t('common.cancel')}
                </Button>
                <Button
                  variant="destructive"
                  disabled={!deleteConfirmed || deleteAccount.isPending}
                  onClick={handleDelete}
                >
                  {deleteAccount.isPending ? t('settings.danger.deleting') : t('settings.danger.deleteAccount')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
