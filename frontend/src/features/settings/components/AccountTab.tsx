import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { CheckCircle2, MailWarning, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { ApiError } from '@/services/api';
import {
  useMyProfile,
  useUpdateProfile,
  useResendVerification,
  useChangePassword,
  useRequestEmailChange,
  useCancelEmailChange,
} from '../hooks/useSettings';

function ProfileSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-9 w-full" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-9 w-full" />
    </div>
  );
}

export function AccountTab() {
  const { t } = useTranslation();
  const { data: profile, isLoading } = useMyProfile();
  const updateProfile = useUpdateProfile();
  const resendVerification = useResendVerification();
  const changePassword = useChangePassword();
  const requestEmailChange = useRequestEmailChange();
  const cancelEmailChange = useCancelEmailChange();

  const [username, setUsername] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [resendCooldown, setResendCooldown] = useState(0);

  useEffect(() => {
    if (profile) setUsername(profile.username ?? '');
  }, [profile]);

  function handleSaveUsername() {
    if (!username.trim()) return;
    updateProfile.mutate(
      { username: username.trim() },
      {
        onSuccess: () => toast.success(t('settings.account.usernameUpdated')),
        onError: (err) => toast.error(err instanceof ApiError ? err.message : t('settings.account.failedUpdateUsername')),
      },
    );
  }

  function handleResendVerification() {
    resendVerification.mutate(undefined, {
      onSuccess: () => toast.success(t('settings.account.verificationSent')),
      onError: () => toast.error(t('settings.account.failedSendVerification')),
      onSettled: () => {
        setResendCooldown(60);
        const interval = setInterval(() => {
          setResendCooldown((s) => {
            if (s <= 1) { clearInterval(interval); return 0; }
            return s - 1;
          });
        }, 1000);
      },
    });
  }

  function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error(t('settings.account.newPasswordsNoMatch'));
      return;
    }
    if (newPassword.length < 8) {
      toast.error(t('settings.account.passwordTooShort'));
      return;
    }
    changePassword.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => {
          toast.success(t('settings.account.passwordChanged'));
          setCurrentPassword('');
          setNewPassword('');
          setConfirmPassword('');
        },
        onError: (err) => toast.error(err instanceof ApiError ? err.message : t('settings.account.failedChangePassword')),
      },
    );
  }

  function handleRequestEmailChange() {
    if (!newEmail.trim()) return;
    requestEmailChange.mutate(newEmail.trim(), {
      onSuccess: () => {
        toast.success(t('settings.account.verificationSentTo', { email: newEmail.trim() }));
        setShowEmailForm(false);
        setNewEmail('');
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : t('settings.account.failedSendVerification')),
    });
  }

  function handleCancelEmailChange() {
    cancelEmailChange.mutate(undefined, {
      onSuccess: () => toast.success(t('settings.account.emailChangeCancelled')),
      onError: () => toast.error(t('settings.account.failedCancelChange')),
    });
  }

  return (
    <div className="space-y-6">
      {profile && !profile.email_verified && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/30">
          <MailWarning className="mt-0.5 size-5 shrink-0 text-amber-600 dark:text-amber-400" />
          <div className="flex-1 space-y-1">
            <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
              {t('settings.account.emailNotVerifiedTitle')}
            </p>
            <p className="text-sm text-amber-700 dark:text-amber-400">
              {t('settings.account.emailNotVerifiedMessage')}
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={handleResendVerification}
            disabled={resendVerification.isPending || resendVerification.isSuccess || resendCooldown > 0}
            className="shrink-0 border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-300"
          >
            {resendVerification.isSuccess ? t('common.sent') : resendVerification.isPending ? t('common.sending') : resendCooldown > 0 ? `${t('settings.account.resendEmail')} (${resendCooldown}s)` : t('settings.account.resendEmail')}
          </Button>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.account.profileTitle')}</CardTitle>
          <CardDescription>{t('settings.account.profileDescription')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <ProfileSkeleton />
          ) : (
            <>
              <div className="space-y-1.5">
                <Label htmlFor="username">{t('settings.account.usernameLabel')}</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder={t('settings.account.usernamePlaceholder')}
                  maxLength={50}
                />
                <p className="text-xs text-muted-foreground">{t('settings.account.usernameHint')}</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">{t('settings.account.emailLabel')}</Label>
                <div className="flex items-center gap-2">
                  <Input id="email" value={profile?.email ?? ''} readOnly className="flex-1 text-muted-foreground" />
                  {profile?.email_verified ? (
                    <Badge variant="secondary" className="shrink-0 gap-1 text-green-700 dark:text-green-400">
                      <CheckCircle2 className="size-3" />
                      {t('settings.account.verified')}
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="shrink-0 text-amber-700 dark:text-amber-400">
                      {t('settings.account.unverified')}
                    </Badge>
                  )}
                </div>

                {profile?.pending_email && (
                  <div className="flex items-start gap-2.5 rounded-md border border-blue-200 bg-blue-50 px-3 py-2.5 dark:border-blue-800 dark:bg-blue-950/30">
                    <Clock className="mt-0.5 size-4 shrink-0 text-blue-600 dark:text-blue-400" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-blue-800 dark:text-blue-300">
                        {t('settings.account.pendingEmail', { email: profile.pending_email })}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={handleCancelEmailChange}
                      disabled={cancelEmailChange.isPending}
                      className="shrink-0 h-auto px-2 py-0.5 text-xs text-blue-700 hover:text-blue-900 hover:bg-blue-100 dark:text-blue-400"
                    >
                      {t('common.cancel')}
                    </Button>
                  </div>
                )}

                {!profile?.pending_email && (
                  <>
                    {showEmailForm ? (
                      <div className="space-y-2">
                        <Input
                          type="email"
                          value={newEmail}
                          onChange={(e) => setNewEmail(e.target.value)}
                          placeholder="new@example.com"
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={handleRequestEmailChange}
                            disabled={requestEmailChange.isPending || !newEmail.trim()}
                          >
                            {requestEmailChange.isPending ? t('common.sending') : t('settings.account.sendVerification')}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => { setShowEmailForm(false); setNewEmail(''); }}
                          >
                            {t('common.cancel')}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowEmailForm(true)}
                        disabled={!profile?.email_verified}
                      >
                        {t('settings.account.changeEmail')}
                      </Button>
                    )}
                    {!profile?.email_verified && !showEmailForm && (
                      <p className="text-xs text-muted-foreground">{t('settings.account.verifyFirstHint')}</p>
                    )}
                  </>
                )}
              </div>

              <Button
                onClick={handleSaveUsername}
                disabled={updateProfile.isPending || !username.trim()}
              >
                {updateProfile.isPending ? t('common.saving') : t('settings.account.saveProfile')}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.account.passwordTitle')}</CardTitle>
          <CardDescription>{t('settings.account.passwordDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="current-password">{t('settings.account.currentPassword')}</Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            <Separator />
            <div className="space-y-1.5">
              <Label htmlFor="new-password">{t('settings.account.newPassword')}</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirm-password">{t('settings.account.confirmNewPassword')}</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <Button
              type="submit"
              disabled={changePassword.isPending || !currentPassword || !newPassword || !confirmPassword}
            >
              {changePassword.isPending ? t('common.saving') : t('settings.account.changePassword')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
